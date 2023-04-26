import asyncio
import kubernetes_asyncio
from kubernetes_asyncio import config, client

from kubernetes_asyncio.client import (
    V1ObjectMeta,
    V1Secret,
    V1PersistentVolume,
    V1PersistentVolumeClaim,
    V1ResourceRequirements,
    V1LabelSelector,
    V1CSIPersistentVolumeSource,
    V1PersistentVolumeSpec,
    V1PersistentVolumeClaimSpec,
    V1Namespace,
    V1ServiceAccount,
    V1RoleBinding,
    V1RoleRef,
    V1Subject,
    V1ClusterRole,
    V1PolicyRule,
    ApiException,
)

async def check_pvc(home_pvc_name, namespace):
    async with kubernetes_asyncio.client.ApiClient() as api_client:
        v1 = kubernetes_asyncio.client.CoreV1Api(api_client)
        pvcs = await v1.list_namespaced_persistent_volume_claim(namespace)
        for claim in pvcs.items:
            if claim.metadata.name == home_pvc_name:
                return claim
        return None

async def delete_pvc(namespace, pvc):
    async with kubernetes_asyncio.client.ApiClient() as api_client:
        v1 = kubernetes_asyncio.client.CoreV1Api(api_client)
        await v1.delete_namespaced_persistent_volume_claim(name=pvc, namespace=namespace)
        await asyncio.sleep(1)

async def create_pvc(home_pvc_name, home_pv_name, namespace, storage_class, capacity):
    pvc = V1PersistentVolumeClaim()
    pvc.api_version = "v1"
    pvc.kind = "PersistentVolumeClaim"
    pvc.metadata = V1ObjectMeta()
    pvc.metadata.name = home_pvc_name
    pvc.spec = V1PersistentVolumeClaimSpec()
    pvc.spec.access_modes = ['ReadWriteMany']
    pvc.spec.resources = V1ResourceRequirements()
    pvc.spec.resources.requests = {"storage": capacity}
    pvc.spec.storage_class_name = storage_class
    if storage_class != "nfs-csi":
        pvc.spec.selector = V1LabelSelector()
        pvc.spec.selector.match_labels = {"name": home_pv_name}
    try:
      async with kubernetes_asyncio.client.ApiClient() as api_client:
        v1 = kubernetes_asyncio.client.CoreV1Api(api_client)
        x = await v1.create_namespaced_persistent_volume_claim(namespace, pvc)
        await asyncio.sleep(1)
    except ApiException as e:
      if re.search("object is being deleted:", e.body):
        raise web.HTTPError(401, "Can't delete PVC {}, please contact administrator!".format(home_pvc_name))
        return False
    return True

def add_volume(spawner_vol_list, volume, volname):
    volume_exists = False
    for vol in spawner_vol_list:
        if "name" in vol and vol["name"] == volname:
            volume_exists = True
    if not volume_exists:
        spawner_vol_list.append(volume) 

def mount(spawner, pv, pvc, mountpath):
    volume = {"name": pv, "persistentVolumeClaim": {"claimName": pvc}}
    volume_mount = {"mountPath": mountpath, "name": pv}
    if len(spawner.volumes) == 0:
        spawner.volumes = [volume]
    else:
        add_volume(spawner.volumes, volume, pv)
    if len(spawner.volume_mounts) == 0:
        spawner.volume_mounts = [volume_mount]
    else:
        add_volume(spawner.volume_mounts, volume_mount, pvc)

async def mount_persistent_hub_home(spawner, username, namespace):
    hub_home_name = username + "-home-default"

    if spawner.user_options.get('delhome') == "delete":
        pvc = await check_pvc(hub_home_name, namespace)
        if pvc:
          await delete_pvc(namespace, hub_home_name)
        await create_pvc(hub_home_name, hub_home_name + "-pv", namespace, "nfs-csi", "10Gi")
    else:
      pvc = await check_pvc(hub_home_name, namespace)
      if not pvc:
        await create_pvc(hub_home_name, hub_home_name + "-pv", namespace, "nfs-csi", "10Gi")

    mount(spawner, hub_home_name + "-pv", hub_home_name, "/home/jovyan")
 

async def bootstrap_pre_spawn(spawner):
  config.load_incluster_config()
  namespace = spawner.namespace
  username = spawner.user.name
  original = username
  if "-" in username:
      username = username.replace("-", "-2d")
  if "_" in username:
      username = username.replace("_", "-5f")

  spawner.environment = {"JUPYTERHUB_API_URL": "http://hub.krenek-ns.svc.cluster.local:8081/hub/api",
                         "JUPYTERHUB_ACTIVITY_URL": "http://hub.krenek-ns.svc.cluster.local:8081/hub/api/users/"+username+"/activity"}

  await mount_persistent_hub_home(spawner, username, namespace)

  if "--SingleUserNotebookApp.max_body_size=6291456000" not in spawner.args:
          spawner.args.append("--SingleUserNotebookApp.max_body_size=6291456000")

  gpu = spawner.user_options.get('gpu')
  cpu = spawner.user_options.get('cpu')
  mem = spawner.user_options.get('mem')
  image = spawner.user_options.get('container_image')

  spawner.image = 'ljocha/gromacs-hub'
  spawner.cpu_limit = 1.
  spawner.cpu_guarantee = .2
  spawner.mem_limit = '8G'
  spawner.mem_guarantee = '4G'

c.KubeSpawner.pre_spawn_hook = bootstrap_pre_spawn
c.KubeSpawner.enable_user_namespaces = False
