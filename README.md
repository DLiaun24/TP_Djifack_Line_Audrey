# TP d'ESXi
La gestion des machines virtuelles avec VMware ESXi.
## Description

L'objectif global de ce TP est d'apprendre à automatiser la création et la gestion de machines virtuelles (MV) dans un environnement VMware vSphere à l'aide de la bibliothèque PyVmomi. 
Cela inclut le déploiement d'images OVA, le clonage de machines virtuelles existantes et la création de nouvelles machines virtuelles à partir de zéro, 
tout en utilisant des fichiers de configuration JSON pour spécifier les paramètres.


## Orientation technique (TP)
### Configuration
L'ESXi mis à disposition : 
* Adresse : 10.144.208.233
* Nom d'utilisateur : root
* Mot de passe: toto32..
### Connexion
Pour établir la connectivité entre notre machine physique et la machine à distance, nous avons utilisé le protocole Wireguard (connexion VPN).
Nous avons utilisé deux commandes principales, suite à l'établissement de la connectivité VPN (utilisation du protocole Wireguard et importation du fichier de configuration: `student1.conf` )
- Connexion à Wireguard VPN : `nmcli connection up student1`
- Déconnexion à Wireguard VPN : `nmcli connection down student1`

## Définition des concepts clés 

1. VMware ESXi : 
    
    VMware ESXi est un hyperviseur de type 1 qui permet de créer et de gérer des machines virtuelles sur un serveur physique. 
Il fonctionne directement sur le matériel sans nécessiter un système d'exploitation sous-jacent, ce qui le rend très efficace pour la virtualisation.
ESXi permet aux entreprises de consolider plusieurs machines virtuelles (MV) sur un seul serveur physique.

2. vCenter :
    
    vCenter Server est une application de gestion centralisée pour les environnements VMware. 
Il permet de gérer plusieurs hôtes ESXi et leurs machines virtuelles à partir d'une interface unique. 
vCenter offre des fonctionnalités avancées telles que la migration de machines virtuelles (vMotion), la gestion des ressources et la haute disponibilité.

3. Datacenter  :

    Un datacenter dans l'environnement VMware est une entité logique qui regroupe des hôtes ESXi, des machines virtuelles, des datastores et d'autres objets de gestion. 
Il sert de conteneur pour organiser et gérer les ressources virtuelles.
En tant que centre de gestion centralisée, vCenter Server permet aux administrateurs de contrôler et de surveiller leur infrastructure virtualisée. Il rationalise les tâches administratives en fournissant une interface unifiée pour gérer plusieurs hôtes ESXi, machines virtuelles et autres ressources.

4. Datastore : 

    Un datastore est un espace de stockage utilisé pour conserver les fichiers des machines virtuelles, tels que les disques virtuels et les fichiers de configuration. 
Les datastores peuvent être basés sur des disques locaux ou sur des systèmes de stockage en réseau (NAS/SAN) et sont accessibles par tous les hôtes ESXi dans un datacenter.

5. vSphere :

    vSphere est la suite de virtualisation de VMware qui inclut ESXi et vCenter Server. 
Elle fournit une plateforme complète pour la gestion des infrastructures virtuelles, permettant aux entreprises de déployer, 
gérer et sécuriser des environnements virtuels.

6. pyVmomi :

    pyVmomi est un SDK Python pour l'API de gestion de VMware vSphere. 
Il permet aux développeurs d'interagir avec vCenter et ESXi pour automatiser des tâches de gestion, 
comme la création de machines virtuelles ou la gestion des datastores, en utilisant des scripts Python.
7. Disques SCSI :

    Les disques SCSI sont des dispositifs de stockage attachés à la machine virtuelle via le contrôleur SCSI.
8. Les contrôleurs SCSI :
    
    Les controleurs SCSI sont des dispositifs qui permettent aux machines virtuelles d'accéder aux disques SCSI.
9. Fichiers avec extensions .OVA (Open Virtual Appliance) :

    Ce sont des archives (fichier TAR comrpessé), qui contiennent une machine virtuelle préconfigurée.
    Ce format est largement utilisé pour faciliter le déploiement et la distribution des machines virtuelles dans des environnements de virtualisation , comme VMware, VirtualBox et d'autres hyperviseurs.
10. Fichier avec exention .ovf (Open Virtualization Format):

    Il s'agit de l'une des caractéristique des fichiers .ova, le fichier de configuration
qui décrit les paramètres de la machine virtuelle (comme le nombre de processeurs, la RAM, etc).

11. Disques Virtuels:

    Il s'agit de l'une des caractéristique des fichiers .ova, ils contiennent les données de la machine virtuelle (souvent au format VMDK pour VMware).

**NB**: Dans notre cas nous avons un seul hôte ESXi. L'interface qui s'afffiche lorsque nous nous connectons à un hôte ESXi est celle de l'application vCenter.
## Analyse des questions

- Automatisation avec PyVmomi :
        
    Comprendre comment PyVmomi permet l'automatisation des tâches liées à la gestion des machines virtuelles dans un environnement vSphere. Cela inclut la création, la modification et la gestion de VM via des scripts Python, réduisant ainsi la charge de travail des administrateurs système.

- Déploiement d'une image OVA (tinyVM) :
    
    Apprendre à déployer une image OVA sur un hôte ESXi. Le fichier de configuration JSON spécifie le nombre d'instances à déployer, ce qui démontre comment automatiser le déploiement de plusieurs VM à partir d'une seule image de base.

- Clonage d'instances OVA :
    
    Comprendre le processus de clonage de VM à partir d'une image OVA existante. Le fichier de configuration JSON indique le nombre de clones à créer, illustrant ainsi l'efficacité de la gestion des ressources et la réduction des temps de déploiement.

- Création de VM from scratch :
       
    Explorer la création de machines virtuelles à partir de zéro en définissant des paramètres spécifiques dans un fichier de configuration JSON. Les paramètres incluent la mémoire RAM, la taille du disque et la configuration du CD-ROM, ce qui montre la flexibilité et le contrôle qu'offre PyVmomi pour personnaliser les VM.

## Bibliothèques à installer
En plus de pyVmomi, nous avons dû installer en entrant :
```bash
pip install paramiko
pip install six
pip install ssl
```


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
  * `host` : Adresse IP de l'ordinateur distant
  * `password` : Mot de passe de l'utilisateur
  * `username` : Nom d'utilisateur
  * `port` : Port pour SSH
* `ova.json` :  qui indique le nombre de machine virtuelle à cloner:
  * `num_instances` : Nombre d'instance de la machine à cloner
  * `ova_path` : Chemin d'accés de la machine originale, celle qui sera cloner suivant le nombre d'instance mentionnée
* `vm_clone.json` : qui comprend les données de configuration pour créer une machine virtuelle à savoir: ram,cum_cpu,cdrom,vm_name et le disk. 
  * `disk_size` : Taille du disque en Mo (Mega Octects). 
  * `ram` : Taille en Mo (Mega Octects)
  * `cdrom` : Chemin d'accès à l'ISO / [datastore1]/test/Core-5.4.iso
  * `cpu` : Nombre de vCPUs
  * `vm_name` : Nom de la machine virtuelle créée
  * `disk_type` : Type du disque dur - thin
## Script `utils.py`
Ce script comprend des fonctions nécessaires au bon déroulement de l'exécution des programmes relatifs à chaque question du TP.

Il permet de gérer des machines virtuelles et des services sur un hôte ESXi. 
Il comprend des fonctions pour : 
- Lire des fichiers de configuration (fichiers au format json), 
- Vérifier et gérer le service SSH, 
- Exécuter des commandes à distance via SSH,
- Se connecter à l'infrastructure VMware pour récupérer des informations sur les machines virtuelles.

## Script `deploy_vm.py`

**NB :** Résolution à la question 7 du TP.

Ce script permet de déployer une machine virtuelle à partir d'un fichier OVA, dans un environnement VMware en utilisant l'API vSphere. 
- Il gère la connexion à un serveur vCenter, lit les configurations à partir d'un fichier JSON, et crée des instances de machines virtuelles à partir de l'OVA spécifiée. 
- L'importation et le téléchargement des disques sont effectués de manière asynchrone, tout en mettant à jour l'utilisateur sur l'état de la progression.
- Encapsulent la logique de traitement des fichiers locaux et distants (Les classes OvfHandler, FileHandle, et WebHandle), assurant une gestion claire des ressources et des erreurs.

Il se lance avec en utilisant Python 3 via cette commande sur une distribution Linux :
```bash
$ python3 deploy_vm.py
```

## Script `clone.py`
**NB:** La fonction de clonage de VM est disponible pour les machines virtuelles gérées par vCenter Server.
Mais vous pouvez également cloner des machines virtuelles exécutées sur un hôte VMware ESXi, par exemple, si vous utilisez une version gratuite de VMware ESXi.
Il est recommandé de :

**Approche de résolution à la question 8 du TP**

Tout d'abord, cloner, c'est créer une copie identique d'une machine virtuelle existante. La nouvelle machine n'a pas besoin d'être configurée à partir de zéro,
car elle possède le même matériel virtuel, les logiciels installées et d'autres paramètres que l'original.
Le clonage de manière simple consiste à copier les fichiers de disques virtuels VMDK  et le fichier de configuration VMX de la machine source dans le répertoire de destination du clone de la VM (datastore).

Ensuite, il faut modifier le fichier VMX du clone pour remplacer les occurrences du nom de la VM source par le nom du clone et pour terminer enregistre la nouvelle machine virtuelle (clone) auprès de vCenter en utilisant le fichier VMX modifié.

**Résolution de la question 8**

Ici nous clonons les machines virtuelles, deployées à partir de fichiers OVA (utilisation de la fonction `deploy`, présente dans le script `deploy_vm.py`).
Le script `clone.py` permet de déployer des machines virtuelles à partir de fichiers OVA, puis clone ces machines virtuelles sur un serveur vSphere. 

Il gère également la connexion à vCenter, l'importation de la VM, la création de répertoires pour les clones, la copie des disques virtuels et l'enregistrement des clones dans vCenter.

Il se lance en utilisant Python 3 via cette commande sur une distribution Linux :
```bash
$ python3 clone.py
```

## Script `create_vm.py`
**NB:** Approche de résolution à la question 9 du TP.

Ce script permet d'automatiser la création et la configuration d'une machine virtuelle (VM). 
Il crée une machine virtuelle vide ,avec des ressources spécifiées dans le fichier de configuration vm_conf.json (les valeurs y sont fixées, et c'est pour ça qu'on a 1 vCPU avec 128 Mo de RAM, une taille disques etc, sinon ce serait différent) et attache éventuellement un CD-ROM avec une image ISO. 

Il effectue les tâches suivantes :

- Connexion à vCenter : Établit une connexion au serveur vCenter.
- Lecture de la configuration de la VM : Récupère les paramètres de configuration de la VM à partir d'un fichier JSON.
- Création d'une VM dummy : Configure une nouvelle VM avec des ressources spécifiées.
- Ajout d'un contrôleur SCSI : Configure un contrôleur SCSI ParaVirtual pour la VM.
- Ajout d'un disque : Alloue un nouveau disque virtuel à la VM en fonction des données de configuration.
- Configuration d'un CD-ROM : Attache éventuellement un lecteur de CD-ROM, qui peut être configuré pour pointer vers un fichier ISO.
- Mise sous tension de la VM : Enfin, met sous tension la VM nouvellement créée.

**Caractéristiques de la VM créée à partir de zéro**

Lorsque la VM est créée à l'aide de ce script, elle possède les caractéristiques suivantes basées sur les données de configuration fournies :

- Nom de la VM : Spécifié dans la configuration JSON.
- Mémoire : Définie selon la valeur spécifiée dans la configuration (par exemple, 128 Mo).
- Nombre de processeurs : Défini dans la configuration (par exemple, 1 vCPU).
- Système d'exploitation invité : Configuré comme *dosGuest*, ce qui indique qu'il est destiné aux systèmes basés sur DOS.
- Configuration du disque 
- Contrôleur SCSI : Un contrôleur SCSI ParaVirtual est ajouté, permettant un accès disque efficace.
- Disque virtuel : Un nouveau disque virtuel est créé avec une taille spécifiée (par exemple, 1 Go) et peut être configuré en tant que provisionné fin (thin provisioned) selon les données de configuration.
- Lecteur de CD-ROM : Éventuellement, un lecteur de CD-ROM peut être ajouté à la VM, qui peut être connecté à un fichier ISO.


Il se lance en utilisant Python 3 via cette commande sur une distribution Linux :
```bash
$ python3 create_vm.py
```
## Liens utilisés
Nous avons manipulé les objets du Managed Object Browser (MOB) accessible à l'adresse http://10.144.208.233/mob. Cette interface nous a permis d'explorer et d'interagir avec divers objets liés à notre infrastructure VMware. 
Nous présentons ci-dessous les différents liens web ayant guidés notre démarche et résolution :


* [Guide pour configurer le client WireGuard sur Ubuntu](https://developerinsider.co/how-to-set-up-wireguard-client-on-ubuntu/amp/)
    
* [Script pour déployer un OVA avec pyVmomi deploy_ova.py](https://github.com/vmware/pyvmomi-community-samples/blob/master/samples/deploy_ova.py)

* [Script pour ajouter un disque à une VM avec pyVmomi](https://github.com/vmware/pyvmomi-community-samples/blob/master/samples/add_disk_to_vm.py)
    
* [Étapes pour cloner des VMs avec et sans vCenter (Cloning VMs in VMware ESXi)](https://search.app/?link=https%3A%2F%2Fwww%2Enakivo%2Ecom%2Fblog%2Fvmware%2Desxi%2Dclone%2Dvm%2F&utm_campaign=57165%2Dor%2Digacx%2Dweb%2Dshrbtn%2Diga%2Dsharing&utm_source=igadl%2Cigatpdl%2Csh%2Fx%2Fgs%2Fm2%2F5)

* [API vSphere Web Services, vSphere Web](https://developer.broadcom.com/xapis/vsphere-web-services-api/latest)
* [Activer SSH sur un hôte ESXi via l'API PyVim / PyVmomi](https://search.app/?link=https%3A%2F%2Fstackoverflow%2Ecom%2Fquestions%2F44729507%2Fenable%2Dssh%2Don%2Dhost%2Dvia%2Dpyvim%2Dpyvmomi%2Dapi&utm_campaign=57165%2Dor%2Digacx%2Dweb%2Dshrbtn%2Diga%2Dsharing&utm_source=igadl%2Cigatpdl%2Csh%2Fx%2Fgs%2Fm2%2F5)
* [Exemples de contributions communautaires pour la bibliothèque pyVmomi pyvmomi-community-samples](https://search.app/?link=https%3A%2F%2Fgithub%2Ecom%2Fvmware%2Fpyvmomi%2Dcommunity%2Dsamples%2Fblob%2Fmaster%2Fsamples%2Fadd%5Fdisk%5Fto%5Fvm%2Epy&utm_campaign=57165%2Dor%2Digacx%2Dweb%2Dshrbtn%2Diga%2Dsharing&utm_source=igadl%2Cigatpdl%2Csh%2Fx%2Fgs%2Fm2%2F5)
* [vSphere : Qu’est-ce que c’est et quelles sont ses principales caractéristiques ?](https://www.ninjaone.com/fr/it-hub/endpoint-management/vsphere-c-est-quoi-fonctionnalites/)
* [Ajout de contrôleurs et disques SCSI avec PyVmomi](https://demitasse.co.nz/2018/06/adding-scsi-controllers-and-disks-with-pyvmomi/)