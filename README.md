# TP d'ESXi
La gestion des machines virtuelles avec VMware ESXi
## Description
Le but de ce dépôt est de familiariser les utilisateurs avec la gestion des machines virtuelles (VM) et des services sur un serveur ESXi ou vCenter à l'aide de scripts Python(Manipulation de la bibliothéque python : PyVmomi). 'ensemble des scripts développés permet d'automatiser des tâches courantes liées à l'infrastructure VMware, facilitant ainsi la gestion et la configuration des VM...

PyVmomi est une bibliothèque Python qui fournit une interface de programmation d'applications (API) permettant d'interagir avec l'API vSphere de VMware.

## Orientation Technique (TP)
Nous avons utilisé dans le cadre de ce Tp, nous avons utiliser l'ESXi mis à la disposition: 10.144.208.233, de nom d'hôte: root, et de mot de passe: toto32..
Pour établir cette connectivité entre notre machine physique et la machine à distance, nous avons utilisé le protocole Wireguard (connection VPN).
Nous avons utiliser deux commandes principales, suite à l'établissement de la connectivité VPN (utilisation du protocole Wireguard et importation du fichier de configuration: student1.conf),
A savoir:
    -Connect from Wireguard VPN: nmcli connection up student1
    -disconnect from Wireguard VPN: nmcli connection down student1
## Structure du projet
```
|- json
|   |- conf.json
|   |- ova.json
|   |- vm_conf.json
|- clone.py
|- create_vm.py
|- deploy_vm.py
|- README.md
|- utils.py
```
## Dossier `json`
Ce dossier comprend l'ensemble des fichiers JSON utilisés lors de ce TP : 
* `conf.json` : qui comprend les informations nécessaires à la connexion au serveur ESXi.
* `ova.json` : ce JSON configure une tâche qui consiste à déployer deux instances d'une machine virtuelle à partir du fichier OVA spécifié.
* `vm_clone.json` : qui comprend les données de configuration pour créer une machine virtuelle à savoir: ram,cum_cpu,cdrom,vm_name et le disk.

## Script `utils.py`
Ce script comprend des fonctions nécessaires au bon déroulement de l'exécution des programmes relatifs à chaque question du TP.
Il permet de gérer des machines virtuelles et des services sur un serveur ESXi ou vCenter. Il inclut des fonctions pour lire des configurations à partir d'un fichier JSON, vérifier et gérer le service SSH, exécuter des commandes à distance via SSH, et récupérer des informations sur des machines virtuelles. L'automatisation de ces tâches facilite la gestion de l'infrastructure VMware.

## Script `deploy_vm.py`

NB: Approche de résolution à la question 7 du TP.

Ce script permet de déployer des fichiers OVA (Open Virtualization Archive) dans un environnement VMware en utilisant l'API vSphere. Il gère la connexion à un serveur vCenter, lit les configurations à partir d'un fichier JSON, et crée des instances de machines virtuelles à partir de l'OVA spécifiée. L'importation et le téléchargement des disques sont effectués de manière asynchrone, tout en mettant à jour l'utilisateur sur l'état de la progression.

```bash
$ python3 deploy_vm.py
```

## Script `clone.py`
NB: Approche de résolution à la question 8 du TP.

Ce script, permet de déployer un OVA puis de la cloner à partir d'un fichier JSON comprenant le chemin d'accès au fichier OVA et le nombres d'instances de VMs que l'on souhaite avoir.
EN effet: Après avoir déployé la VM initiale, le code gère la création de clones en copiant les disques virtuels et en modifiant les fichiers de configuration nécessaires. Enfin, il enregistre chaque clone dans vCenter et vérifie que le service SSH est opérationnel sur les VM clonées.

Se lance avec en utilisant Python 3 via cette commande sur une distribution Linux :
```bash
$ python3 clone.py
```

## Script `create_vm.py`
NB: Approche de résolution à la question 9 du TP.

Ce script permet:automatiser la création et la configuration d'une machine virtuelle (VM). Il crée une VM fictive avec des ressources spécifiées (1 vCPU et 128 Mo de RAM) et attache éventuellement un CD-ROM avec une image ISO. Le code comprend des fonctions pour attendre l'achèvement des tâches, trouver des contrôleurs IDE libres et gérer des périphériques virtuels. Enfin, il met sous tension la VM créée et confirme son lancement réussi. Cette automatisation simplifie le processus de gestion des VM dans un environnement vSphere.

Se lance avec en utilisant Python 3 via cette commande sur une distribution Linux :
```bash
$ python3 create_vm.py
```

## Liens Utilisés
Nous avons manipulé les objets du Managed Object Browser (MOB) accessible à l'adresse http://10.144.208.233/mob. Cette interface nous a permis d'explorer et d'interagir avec divers objets liés à notre infrastructure VMware. 
NOus présentons ci-dessous les différents liens web ayant guidés notre démarche et résolution:

    

    - Guide pour configurer le client WireGuard sur Ubuntu:
    https://developerinsider.co/how-to-set-up-wireguard-client-on-ubuntu/amp/
    
    - Script pour déployer un OVA avec pyVmomi deploy_ova.py:
    https://github.com/vmware/pyvmomi-community-samples/blob/master/samples/deploy_ova.py

    -Script pour ajouter un disque à une VM avec pyVmomi:
    https://github.com/vmware/pyvmomi-community-samples/blob/master/samples/add_disk_to_vm.py
    
    - Étapes pour cloner des VMs avec et sans vCenter (Cloning VMs in VMware ESXi)
     Source : NAKIVO https://search.app/?link=https%3A%2F%2Fwww%2Enakivo%2Ecom%2Fblog%2Fvmware%2Desxi%2Dclone%2Dvm%2F&utm_campaign=57165%2Dor%2Digacx%2Dweb%2Dshrbtn%2Diga%2Dsharing&utm_source=igadl%2Cigatpdl%2Csh%2Fx%2Fgs%2Fm2%2F5

    - API vSphere Web Services, vSphere Web:
     https://developer.broadcom.com/xapis/vsphere-web-services-api/latest
    - Activer SSH sur un hôte ESXi via l'API PyVim / PyVmomi:
    Source : Stack Overflow https://search.app/?link=https%3A%2F%2Fstackoverflow%2Ecom%2Fquestions%2F44729507%2Fenable%2Dssh%2Don%2Dhost%2Dvia%2Dpyvim%2Dpyvmomi%2Dapi&utm_campaign=57165%2Dor%2Digacx%2Dweb%2Dshrbtn%2Diga%2Dsharing&utm_source=igadl%2Cigatpdl%2Csh%2Fx%2Fgs%2Fm2%2F5
    - Exemples de contributions communautaires pour la bibliothèque pyVmomi pyvmomi-community-samples:
    Source : GitHub https://search.app/?link=https%3A%2F%2Fgithub%2Ecom%2Fvmware%2Fpyvmomi%2Dcommunity%2Dsamples%2Fblob%2Fmaster%2Fsamples%2Fadd%5Fdisk%5Fto%5Fvm%2Epy&utm_campaign=57165%2Dor%2Digacx%2Dweb%2Dshrbtn%2Diga%2Dsharing&utm_source=igadl%2Cigatpdl%2Csh%2Fx%2Fgs%2Fm2%2F5


## Perspectives
Pour ce qui est de la question 9 du TP, nous avons configurer notre machine virtuelle, sans le paramètre disk au sein du script create_vm.py:
Dont le code d'ajout au fichier create_vm.py est le suivant:
### Ajouter un disque virtuel à la configuration de la VM

```python
disk_size = data["disk_size"]  # Taille du disque, par défaut à 20 Go si non spécifiée
disk = vim.vm.device.VirtualDisk()
disk.key = 0
disk.deviceInfo = vim.Description(label="Disque dur", summary="Disque virtuel")
disk.capacityInKB = disk_size * 1024 * 1024  # Conversion de Go en Ko
disk.controllerKey = 1000  # Clé du contrôleur IDE pour le premier disque
disk.unitNumber = 0  # Premier disque
disk.backing = vim.vm.device.VirtualDisk.FlatVer2BackingInfo(
    diskMode='persistent',
    fileName=f"{datastore_path}/{data['vm_name']}/{data['vm_name']}.vmdk"
)
config.deviceChange = [vim.vm.device.VirtualDeviceConfigSpec(device=disk, operation='add')]

# Créer un VirtualDeviceConfigSpec pour le disque
disk_spec = vim.vm.device.VirtualDeviceConfigSpec(device=disk, operation=vim.vm.device.VirtualDeviceSpec.Operation.add)
# Assigner le spécimen de disque à la liste deviceChange
config.deviceChange = [disk_spec]   

