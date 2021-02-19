# GCLOUD RUN

## BUILD AN IMAGE
```
docker build -t random:latest
```
```
docker run -it -p 80:80 random
```

## PUSH THE IMAGE TO GCR

Set project
```
gcloud config set project splendid-flow-290316
```

Tag image
```
docker tag random gcr.io/splendid-flow-290316/random
```

Push Image
```
docker push  gcr.io/splendid-flow-290316/random
```

View images 
```
gcloud container images list
```
Deploy
```
gcloud run deploy random --port 80 --platform=managed --allow-unauthenticated --region=us-central1 --image=gcr.io/splendid-flow-290316/random@sha256:fc55f20866f91f94315811b85d1db165d8b2658e5e3940a61c36f7e456d74408 
```

## Deu ruim 

```
Google Cloud Build + Google Cloud Run: Fixing “ERROR: (gcloud.run.deploy) PERMISSION_DENIED: The caller does not have permission”
```

```
# Config
GC_PROJECT=splendid-flow-290316
GC_PROJECT_NUMBER=290316

# Grant the Cloud Run Admin role to the Cloud Build service account
gcloud projects add-iam-policy-binding $GC_PROJECT \
  --member "serviceAccount:$GC_PROJECT_NUMBER@cloudbuild.gserviceaccount.com" \
  --role roles/run.admin

# Grant the IAM Service Account User role to the Cloud Build service account on the Cloud Run runtime service account
gcloud iam service-accounts add-iam-policy-binding \
  $GC_PROJECT_NUMBER-compute@developer.gserviceaccount.com \
  --member="serviceAccount:$GC_PROJECT_NUMBER@cloudbuild.gserviceaccount.com" \
  --role="roles/iam.serviceAccountUser"
```

https://cloud.google.com/cloud-build/docs/deploying-builds/deploy-cloud-run#required_iam_permissions


## Listar Bms


```
curl https://bms-e24zyhbnkq-uc.a.run.app/ -H "Content-Type:application/json" -H "X-UID:7P7XMLKzHwQIjb9q5SgQDUd9bLm1" 
```
