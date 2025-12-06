#!/bin/bash

# --- CONFIGURATION ---
APP_NAME="miso-brain"
DB_NAME="miso-db"
PVC_NAME="postgres-pvc"
VERSION_TAG="10-2-2025"

# !!! UPDATED IMAGE NAME !!!
# Assuming your image is named 'miso-brain' and using the tag from your prompt
IMAGE_NAME="localhost:32000/miso-brain:$VERSION_TAG"

echo "#####################################################"
echo "###   MISO FACTORY RESET: $VERSION_TAG   ###"
echo "#####################################################"

# 1. TEAR DOWN
echo "[1/6] Deleting existing Kubernetes resources..."
microk8s kubectl delete deployment $APP_NAME $DB_NAME --ignore-not-found
microk8s kubectl delete service $APP_NAME $DB_NAME --ignore-not-found
microk8s kubectl delete pvc $PVC_NAME --ignore-not-found

# Delete RBAC
microk8s kubectl delete sa miso-brain-sa --ignore-not-found
microk8s kubectl delete role secret-manager --ignore-not-found
microk8s kubectl delete rolebinding miso-brain-binding --ignore-not-found

echo "Waiting 10s for termination..."
sleep 10

# 2. WIPE HOST STORAGE (The Fix)
echo "[2/6] WIPING PHYSICAL STORAGE..."
if ls /var/snap/microk8s/common/default-storage/default-$PVC_NAME-* 1> /dev/null 2>&1; then
    sudo rm -rf /var/snap/microk8s/common/default-storage/default-$PVC_NAME-*
    echo "✅ Storage wiped. Data destroyed."
else
    echo "⚠️ No physical data found (Clean slate)."
fi

# 3. RBAC SETUP
echo "[3/6] creating RBAC..."
cat <<YAML | microk8s kubectl apply -f -
apiVersion: v1
kind: ServiceAccount
metadata:
  name: miso-brain-sa
---
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: secret-manager
rules:
- apiGroups: [""]
  resources: ["secrets"]
  verbs: ["get", "list", "create", "update", "patch"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: miso-brain-binding
subjects:
- kind: ServiceAccount
  name: miso-brain-sa
roleRef:
  kind: Role
  name: secret-manager
  apiGroup: rbac.authorization.k8s.io
YAML

# 4. DATABASE DEPLOY
echo "[4/6] Deploying Postgres..."
cat <<YAML | microk8s kubectl apply -f -
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: $PVC_NAME
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 1Gi
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: $DB_NAME
spec:
  selector:
    matchLabels:
      app: $DB_NAME
  template:
    metadata:
      labels:
        app: $DB_NAME
    spec:
      containers:
      - name: postgres
        image: postgres:15
        env:
        - name: POSTGRES_PASSWORD
          value: "dbpassword"
        - name: POSTGRES_DB
          value: "miso_db"
        volumeMounts:
        - mountPath: /var/lib/postgresql/data
          name: postgres-storage
      volumes:
      - name: postgres-storage
        persistentVolumeClaim:
          claimName: $PVC_NAME
---
apiVersion: v1
kind: Service
metadata:
  name: $DB_NAME
spec:
  ports:
  - port: 5432
  selector:
    app: $DB_NAME
YAML

# 5. APP DEPLOY
echo "[5/6] Deploying App ($IMAGE_NAME)..."
cat <<YAML | microk8s kubectl apply -f -
apiVersion: apps/v1
kind: Deployment
metadata:
  name: $APP_NAME
spec:
  selector:
    matchLabels:
      app: $APP_NAME
  template:
    metadata:
      labels:
        app: $APP_NAME
    spec:
      serviceAccountName: miso-brain-sa
      containers:
      - name: python-app
        image: $IMAGE_NAME
        imagePullPolicy: Always
        env:
        - name: DB_HOST
          value: "$DB_NAME"
        - name: DB_PASS
          value: "dbpassword"
---
apiVersion: v1
kind: Service
metadata:
  name: $APP_NAME
spec:
  selector:
    app: $APP_NAME
  ports:
    - protocol: TCP
      port: 80
      targetPort: 8000
YAML

# 6. VERIFY
echo "[6/6] Done."
microk8s kubectl get pods
