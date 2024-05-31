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



# CWE 79 newer NIST 
https://github.com/AwesomestCode/LiveBot/commit/57505527f838d1e46e8f93d567ba552a30185bfa
https://github.com/EasyCorp/EasyAdminBundle/commit/127436e4c3f56276d548070f99e61b7234200a11 GOOD!
https://github.com/wp-plugins/tfo-graphviz/commit/594c953a345f79e26003772093b0caafc14b92c2
https://github.com/Zimbra/zm-admin-ajax/commit/bb240ce0c71c01caabaa43eed30c78ba8d7d3591
https://github.com/codersclub/DiscuzX/commit/4a9673624f46f7609486778ded9653733020c567
https://github.com/wp-plugins/wp-file-upload/commit/c846327df030a0a97da036a2f07c769ab9284ddb
https://github.com/sequentech/admin-console/commit/0043a6b1e6e0f5abc9557e73f9ffc524fc5d609d
https://github.com/wp-plugins/wp-insert/commit/a07b7b08084b9b85859f3968ce7fde0fd1fcbba3
https://github.com/mintplex-labs/anything-llm/commit/a4ace56a401ffc8ce0082d7444159dfd5dc28834
https://github.com/wp-plugins/wp-spreadplugin/commit/a9b9afc641854698e80aa5dd9ababfc8e0e57d69
https://github.com/l2c2technologies/Koha/commit/950fc8e101886821879066b33e389a47fb0a9782

CWE 89
https://github.com/folio-org/spring-module-core/commit/d374a5f77e6b58e36f0e0e4419be18b95edcd7ff _> java
https://github.com/parisneo/lollms-webui/commit/f0bc8f2babdfd4770a5adbf3b60ec612e4f1db46 -> 15 changed files

CWE 22
https://github.com/qdrant/qdrant/commit/3ab5172e9c8f14fa1f7b24e7147eac74e2412b62"
https://github.com/gradio-app/gradio/commit/16fbe9cd0cffa9f2a824a0165beb43446114eec7
https://github.com/langchain-ai/langchain/commit/aad3d8bd47d7f5598156ff2bdcc8f736f24a7412