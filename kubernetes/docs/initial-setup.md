# Initial Setup (Getting Started)
I have 3 nodes in my HomeLab
| Device                      | Name      | Disk Size |  Ram  | CPU        | Operating System  | Purpose              |
|-----------------------------|-----------|-----------|-------|------------|-------------------|----------------------|
| Mini PC 1                   | mini1     | 64GB SSD  | 16GB  | 4C/4T      |Ubuntu 24.04.4 LTS | Kubernetes Master 1  |
| Mini PC 2                   | mini2     | 64GB SSD  | 16GB  | 4C/4T      |Ubuntu 24.04.4 LTS | Kubernetes Worker 1  |
| Mini PC 3                   | mini3     | 64GB SSD  | 16GB  | 4C/4T      |Ubuntu 24.04.4 LTS | Kubernetes Worker 2  |

---

<br>

## Setting up the Cluster
I am using Kubespray to deploy Kubernetes in my HomeLab. My custom variables for the cluster & hosts (inventory) file can be found under `kubernetes/kubespray`

### Pre Settings for all nodes
Before running kubespray ansible, all of the nodes should be prepared with the following steps: 
- Create a root password (same for all nodes in my case)
- Update `/etc/ssh/sshd_config` file and uncomment the `PermitRootLogin yes` option within the file (for root SSH into all nodes)
-  Restart sshd service using systemctl

### Running Kubespray 
Running the docker command for kubespray
```bash
$ docker run --rm -it --mount type=bind,source="$(pwd)"/hosts.yml,dst=/inventory --mount type=bind,source="$(pwd)"/vars.yml,dst=/vars quay.io/kubespray/kubespray:v2.31.0 bash
```
<br>

Once inside the Kubespray container, run the following ansible command to verify if the container can reach to all nodes via SSH
```bash
$ ansible all -i /inventory -m ping -k
SSH password: 
wk1 | SUCCESS => {
    "ansible_facts": {
        "discovered_interpreter_python": "/usr/bin/python3.12"
    },
    "changed": false,
    "ping": "pong"
}
cp | SUCCESS => {
    "ansible_facts": {
        "discovered_interpreter_python": "/usr/bin/python3.12"
    },
    "changed": false,
    "ping": "pong"
}
wk2 | SUCCESS => {
    "ansible_facts": {
        "discovered_interpreter_python": "/usr/bin/python3.12"
    },
    "changed": false,
    "ping": "pong"
}
```
<br>

Finally, run the kubespray `cluster.yml` file to install kubernetes
```bash
$ ansible-playbook -e @/vars -i /inventory cluster.yml -k
```

<br>


### Verify Kubernetes Cluster
After successful installation, verify the cluster
```bash
## get nodes
➜  ~ k get no
NAME   STATUS   ROLES           AGE   VERSION
cp     Ready    control-plane   23m   v1.35.4
wk1    Ready    <none>          22m   v1.35.4
wk2    Ready    <none>          22m   v1.35.4

## get all pods
➜  ~ k get po -A
NAMESPACE     NAME                                                READY   STATUS    RESTARTS   AGE
argocd        argocd-application-controller-0                     1/1     Running   0          22m
argocd        argocd-applicationset-controller-5cc599989f-l9s4t   1/1     Running   0          22m
argocd        argocd-dex-server-6bd7bd9c68-xbzbs                  1/1     Running   0          22m
argocd        argocd-notifications-controller-658879594b-nncn9    1/1     Running   0          22m
argocd        argocd-redis-6d96789db9-tlmsw                       1/1     Running   0          22m
argocd        argocd-repo-server-579b78689-gnxgn                  1/1     Running   0          22m
argocd        argocd-server-574588fc44-cwxcl                      1/1     Running   0          22m
kube-system   calico-kube-controllers-7c99df9fc4-rlld2            1/1     Running   0          22m
kube-system   calico-node-544j5                                   1/1     Running   0          22m
kube-system   calico-node-q5wgd                                   1/1     Running   0          22m
kube-system   calico-node-stpg7                                   1/1     Running   0          22m
kube-system   coredns-65f48bbb6-92k26                             1/1     Running   0          22m
kube-system   coredns-65f48bbb6-kgh4v                             1/1     Running   0          22m
kube-system   dns-autoscaler-5654b864c-kfvq5                      1/1     Running   0          22m
kube-system   etcd-cp                                             1/1     Running   0          24m
kube-system   kube-apiserver-cp                                   1/1     Running   0          24m
kube-system   kube-controller-manager-cp                          1/1     Running   0          24m
kube-system   kube-proxy-28f5b                                    1/1     Running   0          23m
kube-system   kube-proxy-fz6dz                                    1/1     Running   0          23m
kube-system   kube-proxy-jl7s5                                    1/1     Running   0          23m
kube-system   kube-scheduler-cp                                   1/1     Running   0          24m
kube-system   nginx-proxy-wk1                                     1/1     Running   0          23m
kube-system   nginx-proxy-wk2                                     1/1     Running   0          23m
kube-system   nodelocaldns-g8zl2                                  1/1     Running   0          22m
kube-system   nodelocaldns-nbfrk                                  1/1     Running   0          22m
kube-system   nodelocaldns-q47vn                                  1/1     Running   0          22m
```
