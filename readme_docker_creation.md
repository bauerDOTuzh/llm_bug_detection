# Dockerfile information
- Current dockerfile includes all files including caches, so it makes it easier to analyse


# For creators of this repository
- to build locally dockerfile execute
```bash
docker build -t infile_vulnerability_localization .
```

# to push docker image 
```docker tag infile_vulnerability_localization baueradam/infile_vulnerability_localization:latest```

```docker push baueradam/infile_vulnerability_localization:latest```
