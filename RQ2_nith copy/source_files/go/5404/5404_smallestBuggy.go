{prepend_content}
func joinPath_createDictionary(dst, name string, isDir bool) (string, error) {
    target := filepath.Join(dst, name)
    if isDir {
        if _, err := os.Stat(target); err != nil {
            if err := os.MkdirAll(target, 0755); err != nil {
                return "", err
            }
        }
    }
    return target, nil
}
{append_content}
