VERSION=v0.0.11

docker build --platform linux/amd64 -t tugjabg/os-skkhkt:$VERSION .
docker push tugjabg/os-skkhkt:$VERSION