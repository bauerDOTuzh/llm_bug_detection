# Manual sanitization
# 406
- removed function getFolderContentPreviewAction

# 408
- added files from github

# 405
- new file commit was done december 2023 (might be fine)
- a lot files added from repository

# 3989
- REMOVED escaping of an ID (it could be separate experiment)
```
     const id = `__RQ${React.useId()}`
-    const idJSON = JSON.stringify(id)
+    const idJSON = htmlEscapeJsonString(JSON.stringify(id))
````

# XSS files
-no large changes