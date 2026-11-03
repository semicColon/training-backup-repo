#!/bin/bash

set -e
export PATH=$PATH:/usr/local/bin
AWX_NAMESPACE="awx"
AWX_INSTANCE="awx-demo"
AWX_OPERATOR_VERSION="2.19.1"
echo "======================================"
echo " AWX Installation on K3s "
echo "======================================"
################################################
# Step 1 - Prepare System
################################################
echo "[INFO] Updating system..."
dnf update -y
echo "[INFO] Installing prerequisites..."
dnf install -y git curl tar make
echo "[INFO] Configuring SELinux..."
setenforce 0 || true
sed -i 's/^SELINUX=.*/SELINUX=permissive/' /etc/selinux/config
echo "[INFO] Disabling Firewalld..."

systemctl disable --now firewalld || true

################################################

# Step 2 - Install K3s

################################################

echo "[INFO] Installing K3s..."

curl -sfL https://get.k3s.io | sh -

echo "[INFO] Waiting for K3s..."
for i in {1..30}
do
    if /usr/local/bin/kubectl get nodes 2>/dev/null | grep -q Ready
    then
        echo "[INFO] K3s Ready"
        break
    fi
    echo "[INFO] Waiting... ($i/30)"

    sleep 10

done

echo "[INFO] Nodes"

/usr/local/bin/kubectl get nodes

################################################
# Step 3 - Configure kubectl
################################################
echo "[INFO] Configuring kubectl..."
mkdir -p $HOME/.kube
cp /etc/rancher/k3s/k3s.yaml $HOME/.kube/config
chmod 600 $HOME/.kube/config
export KUBECONFIG=$HOME/.kube/config
/usr/local/bin/kubectl get pods -A


################################################
# Step 4 - Install AWX Operator
################################################
echo "[INFO] Downloading AWX Operator..."
rm -rf awx-operator
git clone https://github.com/ansible/awx-operator.git
cd awx-operator
git checkout ${AWX_OPERATOR_VERSION}
echo "[INFO] Creating namespace..."
/usr/local/bin/kubectl create namespace ${AWX_NAMESPACE} 2>/dev/null || true

echo "[INFO] Deploying AWX Operator..."
make deploy
################################################
# Wait for deployment
################################################
echo "[INFO] Waiting for operator deployment..."
while ! /usr/local/bin/kubectl get deployment awx-operator-controller-manager -n ${AWX_NAMESPACE} >/dev/null 2>&1
do
    sleep 5
done
echo "[INFO] Deployment discovered."
################################################
# Modify deployment YAML
################################################

echo "[INFO] Exporting deployment..."
/usr/local/bin/kubectl get deployment awx-operator-controller-manager -n ${AWX_NAMESPACE} -o yaml > operator.yaml
echo "[INFO] Updating kube-rbac-proxy image..."

sed -i 's|gcr.io/kubebuilder/kube-rbac-proxy:v0.15.0|docker.io/kubebuilder/kube-rbac-proxy:v0.15.0|g' operator.yaml

echo "[INFO] Removing imagePullSecrets..."

sed -i '/imagePullSecrets:/,/redhat-operators-pull-secret/d' operator.yaml
echo "[INFO] Applying deployment changes..."
/usr/local/bin/kubectl apply -f operator.yaml
echo "[INFO] Restarting operator..."
/usr/local/bin/kubectl rollout restart deployment/awx-operator-controller-manager -n ${AWX_NAMESPACE}
/usr/local/bin/kubectl rollout status deployment/awx-operator-controller-manager -n ${AWX_NAMESPACE} --timeout=300s

echo "[INFO] Operator Pods"
/usr/local/bin/kubectl get pods -n ${AWX_NAMESPACE}

################################################
# Step 5 - Create AWX Instance
################################################

echo "[INFO] Creating AWX instance..."


cat > awx-demo.yml <<EOF
apiVersion: awx.ansible.com/v1beta1
kind: AWX
metadata:
  name: awx-demo
  namespace: awx
spec:
  service_type: nodeport
EOF
echo "========== awx-demo.yml =========="

cat awx-demo.yml



echo "================================="



/usr/local/bin/kubectl apply -f awx-demo.yml





echo "[INFO] Verifying AWX resource..."



sleep 5



/usr/local/bin/kubectl get awx -A



if ! /usr/local/bin/kubectl get awx -A | grep -q awx-demo

then

    echo "[ERROR] AWX resource creation failed."

    exit 1

fi







################################################



# Step 6 - Wait for AWX Pods



################################################

echo "[INFO] Waiting for AWX components..."

for i in {1..60}

do



    PODS=$(/usr/local/bin/kubectl get pods -n ${AWX_NAMESPACE}  --no-headers 2>/dev/null | wc -l)



    if [ "$PODS" -gt 3 ]

    then

        break

    fi

    echo "[INFO] Waiting for AWX pods..."



    sleep 15



done



echo "[INFO] Current Pods"





/usr/local/bin/kubectl get pods -n ${AWX_NAMESPACE}



################################################



# Step 7 - Wait for Service



################################################



echo "[INFO] Waiting for AWX service..."



for i in {1..30}

do



    if /usr/local/bin/kubectl get svc ${AWX_INSTANCE}-service -n ${AWX_NAMESPACE} >/dev/null 2>&1

    then

        break

    fi



    sleep 10

done





/usr/local/bin/kubectl get svc -n ${AWX_NAMESPACE}



################################################



# Step 8 - Get URL



################################################



NODEPORT=$(/usr/local/bin/kubectl get svc ${AWX_INSTANCE}-service -n ${AWX_NAMESPACE} -o jsonpath='{.spec.ports[0].nodePort}')







SERVER_IP=$(hostname -I | awk '{print $1}')







################################################



# Step 9 - Get Password



################################################







echo "[INFO] Waiting for admin password secret..."



for i in {1..60}

do

    if /usr/local/bin/kubectl get secret  ${AWX_INSTANCE}-admin-password -n ${AWX_NAMESPACE} >/dev/null 2>&1

    then

        break

    fi

    sleep 10

done



PASSWORD=$(/usr/local/bin/kubectl get secret ${AWX_INSTANCE}-admin-password -n ${AWX_NAMESPACE} -o jsonpath="{.data.password}" | base64 -d)



################################################



# Final Output



################################################







echo ""



echo "======================================"



echo " AWX INSTALLATION COMPLETED "



echo "======================================"



echo ""







echo "URL:"



echo "http://${SERVER_IP}:${NODEPORT}"







echo ""



echo "Username : admin"



echo "Password : ${PASSWORD}"



echo ""







echo "Verify:"



echo "kubectl get awx -A"



echo "kubectl get pods -n awx"



echo "kubectl get svc -n awx"


