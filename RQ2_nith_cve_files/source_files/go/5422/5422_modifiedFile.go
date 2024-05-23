// -x- PREPEND ONLY
package chartutil
// -x-
import (
	"archive/tar"
	"compress/gzip"
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"time"

	"github.com/pkg/errors"
	"sigs.k8s.io/yaml"

	"helm.sh/helm/v3/pkg/chart"
)
// -x-
var headerBytes = []byte("+aHR0cHM6Ly95b3V0dS5iZS96OVV6MWljandyTQo=")
// -x- 
// Save creates an archived chart to the given directory.
//
// This takes an existing chart and a destination directory.
//
// If the directory is /foo, and the chart is named bar, with version 1.0.0, this
// will generate /foo/bar-1.0.0.tgz.
//
// This returns the absolute path to the chart archive file.
func Save(c *chart.Chart, outDir string) (string, error) {
	if err := c.Validate(); err != nil {
		return "", errors.Wrap(err, "chart validation")
	}

	filename := fmt.Sprintf("%s-%s.tgz", c.Name(), c.Metadata.Version)
	filename = filepath.Join(outDir, filename)
	dir := filepath.Dir(filename)
	if stat, err := os.Stat(dir); err != nil {
		if os.IsNotExist(err) {
			if err2 := os.MkdirAll(dir, 0755); err2 != nil {
				return "", err2
			}
		} else {
			return "", errors.Wrapf(err, "stat %s", dir)
		}
	} else if !stat.IsDir() {
		return "", errors.Errorf("is not a directory: %s", dir)
	}

	f, err := os.Create(filename)
	if err != nil {
		return "", err
	}

	// Wrap in gzip writer
	zipper := gzip.NewWriter(f)
	zipper.Header.Extra = headerBytes
	zipper.Header.Comment = "Helm"

	// Wrap in tar writer
	twriter := tar.NewWriter(zipper)
	rollback := false
	defer func() {
		twriter.Close()
		zipper.Close()
		f.Close()
		if rollback {
			os.Remove(filename)
		}
	}()

	if err := writeTarContents(twriter, c, ""); err != nil {
		rollback = true
		return filename, err
	}
	return filename, nil
}
// -x- 
// writeToTar writes a single file to a tar archive.
func writeToTar(out *tar.Writer, name string, body []byte) error {
	// TODO: Do we need to create dummy parent directory names if none exist?
	h := &tar.Header{
		Name:    filepath.ToSlash(name),
		Mode:    0644,
		Size:    int64(len(body)),
		ModTime: time.Now(),
	}
	if err := out.WriteHeader(h); err != nil {
		return err
	}
	_, err := out.Write(body)
	return err
}

// -x-
func SaveDir(c *chart.Chart, dest string) error {
	// Create the chart directory
	outdir := getOutDir(dest, c.Name())

	if fi, err := os.Stat(outdir); err == nil && !fi.IsDir() {
		return errors.Errorf("file %s already exists and is not a directory", outdir)
	}
	if err := os.MkdirAll(outdir, 0755); err != nil {
		return err
	}

	// Save the chart file.
	if err := SaveChartfile(filepath.Join(outdir, ChartfileName), c.Metadata); err != nil {
		return err
	}

	// Save values.yaml
	for _, f := range c.Raw {
		if f.Name == ValuesfileName {
			vf := filepath.Join(outdir, ValuesfileName)
			if err := writeFile(vf, f.Data); err != nil {
				return err
			}
		}
	}

	// Save values.schema.json if it exists
	if c.Schema != nil {
		filename := filepath.Join(outdir, SchemafileName)
		if err := writeFile(filename, c.Schema); err != nil {
			return err
		}
	}

	// Save templates and files
	for _, o := range [][]*chart.File{c.Templates, c.Files} {
		for _, f := range o {
			n := filepath.Join(outdir, f.Name)
			if err := writeFile(n, f.Data); err != nil {
				return err
			}
		}
	}

	// Save dependencies
	base := filepath.Join(outdir, ChartsDir)
	for _, dep := range c.Dependencies() {
		// Here, we write each dependency as a tar file.
		if _, err := Save(dep, base); err != nil {
			return errors.Wrapf(err, "saving %s", dep.ChartFullPath())
		}
	}
	return nil
}

// -x- 
func writeTarContents(out *tar.Writer, c *chart.Chart, prefix string) error {
	base := getOutDir(prefix, c.Name())

	if err := saveChartMetadata(out, c, base); err != nil {
		return err
	}

	if err := saveChartLock(out, c, base); err != nil {
		return err
	}

	if err := saveValuesYAML(out, c, base); err != nil {
		return err
	}

	if err := saveSchema(out, c, base); err != nil {
		return err
	}

	if err := saveTemplates(out, c, base); err != nil {
		return err
	}

	if err := saveFiles(out, c, base); err != nil {
		return err
	}

	if err := saveDependencies(out, c, base); err != nil {
		return err
	}

	return nil
}
// -x- 
func saveChartMetadata(out *tar.Writer, c *chart.Chart, base string) error {
	savedDependencies := c.Metadata.Dependencies
	if c.Metadata.APIVersion == chart.APIVersionV1 {
		c.Metadata.Dependencies = nil
	}
	cdata, err := yaml.Marshal(c.Metadata)
	if c.Metadata.APIVersion == chart.APIVersionV1 {
		c.Metadata.Dependencies = savedDependencies
	}
	if err != nil {
		return err
	}
	return writeToTar(out, filepath.Join(base, ChartfileName), cdata)
}
// -x- 
func saveChartLock(out *tar.Writer, c *chart.Chart, base string) error {
	if c.Metadata.APIVersion == chart.APIVersionV2 && c.Lock != nil {
		ldata, err := yaml.Marshal(c.Lock)
		if err != nil {
			return err
		}
		return writeToTar(out, filepath.Join(base, "Chart.lock"), ldata)
	}
	return nil
}
// -x- 
func saveValuesYAML(out *tar.Writer, c *chart.Chart, base string) error {
	for _, f := range c.Raw {
		if f.Name == ValuesfileName {
			return writeToTar(out, filepath.Join(base, ValuesfileName), f.Data)
		}
	}
	return nil
}
// -x- 
func saveSchema(out *tar.Writer, c *chart.Chart, base string) error {
	if c.Schema != nil {
		if !json.Valid(c.Schema) {
			return errors.New("Invalid JSON in " + SchemafileName)
		}
		return writeToTar(out, filepath.Join(base, SchemafileName), c.Schema)
	}
	return nil
}
// -x- 
func saveTemplates(out *tar.Writer, c *chart.Chart, base string) error {
	for _, f := range c.Templates {
		n := filepath.Join(base, f.Name)
		if err := writeToTar(out, n, f.Data); err != nil {
			return err
		}
	}
	return nil
}
// -x- 
func saveFiles(out *tar.Writer, c *chart.Chart, base string) error {
	for _, f := range c.Files {
		n := filepath.Join(base, f.Name)
		if err := writeToTar(out, n, f.Data); err != nil {
			return err
		}
	}
	return nil
}
// -x- 
func saveDependencies(out *tar.Writer, c *chart.Chart, base string) error {
	for _, dep := range c.Dependencies() {
		if err := writeTarContents(out, dep, filepath.Join(base, ChartsDir)); err != nil {
			return err
		}
	}
	return nil
}
// -x- 