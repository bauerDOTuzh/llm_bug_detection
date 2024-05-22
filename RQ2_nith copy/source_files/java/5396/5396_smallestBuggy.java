{prepend_content}
@Nullable
private FileInput toFileInput(String fileUri, Settings withClauseOptions) {
    URI uri = toURI(fileUri);
    FileInputFactory fileInputFactory = fileInputFactories.get(uri.getScheme());
    if (fileInputFactory != null) {
        try {
            return fileInputFactory.create(uri, withClauseOptions);
        } catch (IOException e) {
            return null;
        }
    }
    return new URLFileInput(uri);
}
{append_content}