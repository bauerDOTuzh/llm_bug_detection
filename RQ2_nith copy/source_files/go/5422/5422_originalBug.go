
// SaveDir saves a chart as files in a directory.
//
// This takes the chart name, and creates a new subdirectory inside of the given dest
// directory, writing the chart's contents to that subdirectory.
func SaveDir(c *chart.Chart, dest string) error {
	// Create the chart directory
	outdir := filepath.Join(dest, c.Name())
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


func writeTarContents(out *tar.Writer, c *chart.Chart, prefix string) error {
	base := filepath.Join(prefix, c.Name())

	// Pull out the dependencies of a v1 Chart, since there's no way
	// to tell the serializer to skip a field for just this use case
	savedDependencies := c.Metadata.Dependencies
	if c.Metadata.APIVersion == chart.APIVersionV1 {
		c.Metadata.Dependencies = nil
	}
	// Save Chart.yaml
	cdata, err := yaml.Marshal(c.Metadata)
	if c.Metadata.APIVersion == chart.APIVersionV1 {
		c.Metadata.Dependencies = savedDependencies
	}
	if err != nil {
		return err
	}
	if err := writeToTar(out, filepath.Join(base, ChartfileName), cdata); err != nil {
		return err
	}

	// Save Chart.lock
	// TODO: remove the APIVersion check when APIVersionV1 is not used anymore
	if c.Metadata.APIVersion == chart.APIVersionV2 {
		if c.Lock != nil {
			ldata, err := yaml.Marshal(c.Lock)
			if err != nil {
				return err
			}
			if err := writeToTar(out, filepath.Join(base, "Chart.lock"), ldata); err != nil {
				return err
			}
		}
	}

	// Save values.yaml
	for _, f := range c.Raw {
		if f.Name == ValuesfileName {
			if err := writeToTar(out, filepath.Join(base, ValuesfileName), f.Data); err != nil {
				return err
			}
		}
	}

	// Save values.schema.json if it exists
	if c.Schema != nil {
		if !json.Valid(c.Schema) {
			return errors.New("Invalid JSON in " + SchemafileName)
		}
		if err := writeToTar(out, filepath.Join(base, SchemafileName), c.Schema); err != nil {
			return err
		}
	}

	// Save templates
	for _, f := range c.Templates {
		n := filepath.Join(base, f.Name)
		if err := writeToTar(out, n, f.Data); err != nil {
			return err
		}
	}

	// Save files
	for _, f := range c.Files {
		n := filepath.Join(base, f.Name)
		if err := writeToTar(out, n, f.Data); err != nil {
			return err
		}
	}

	// Save dependencies
	for _, dep := range c.Dependencies() {
		if err := writeTarContents(out, dep, filepath.Join(base, ChartsDir)); err != nil {
			return err
		}
	}
	return nil
}
