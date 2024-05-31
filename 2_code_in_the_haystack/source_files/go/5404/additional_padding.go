// -x-
//go:build !windows

package file

import (
	"os"
	"syscall"
)

// getXid is the UID GID system info for unix
func getXid(info os.FileInfo) (uid, gid int) {
	uid = -1
	gid = -1
	if stat, ok := info.Sys().(*syscall.Stat_t); ok {
		uid = int(stat.Uid)
		gid = int(stat.Gid)
	}

	return uid, gid
}
// -x-
//go:build windows

package file

import (
	"os"
)

// getXid is a placeholder for windows file information
func getXid(info os.FileInfo) (uid, gid int) {
	return -1, -1
}
// -x-
package file

import "sync/atomic"

var nextID atomic.Uint64 // note: this is governed by the reference constructor

// ID is used for file tree manipulation to uniquely identify tree nodes.
type ID uint64

type IDs []ID

func (ids IDs) Len() int {
	return len(ids)
}

func (ids IDs) Less(i, j int) bool {
	return ids[i] < ids[j]
}

func (ids IDs) Swap(i, j int) {
	ids[i], ids[j] = ids[j], ids[i]
}
// -x-
//nolint:dupl
package file

import "sort"

type IDSet map[ID]struct{}

func NewIDSet(is ...ID) IDSet {
	// TODO: replace with single generic implementation that also incorporates other set implementations
	s := make(IDSet)
	s.Add(is...)
	return s
}

func (s IDSet) Size() int {
	return len(s)
}

func (s IDSet) Merge(other IDSet) {
	for _, i := range other.List() {
		s.Add(i)
	}
}

func (s IDSet) Add(ids ...ID) {
	for _, i := range ids {
		s[i] = struct{}{}
	}
}

func (s IDSet) Remove(ids ...ID) {
	for _, i := range ids {
		delete(s, i)
	}
}

func (s IDSet) Contains(i ID) bool {
	_, ok := s[i]
	return ok
}

func (s IDSet) Clear() {
	// TODO: replace this with the new 'clear' keyword when it's available in go 1.20 or 1.21
	for i := range s {
		delete(s, i)
	}
}

func (s IDSet) List() []ID {
	ret := make([]ID, 0, len(s))
	for i := range s {
		ret = append(ret, i)
	}
	return ret
}

func (s IDSet) Sorted() []ID {
	ids := s.List()

	sort.Slice(ids, func(i, j int) bool {
		return ids[i] < ids[j]
	})

	return ids
}

func (s IDSet) ContainsAny(ids ...ID) bool {
	for _, i := range ids {
		_, ok := s[i]
		if ok {
			return true
		}
	}
	return false
}
// -x-
package file

import (
	"fmt"
	"testing"

	"github.com/stretchr/testify/assert"
)

func TestIDSet_Size(t *testing.T) {
	type testCase struct {
		name string
		s    IDSet
		want int
	}
	tests := []testCase{
		{
			name: "empty set",
			s:    NewIDSet(),
			want: 0,
		},
		{
			name: "non-empty set",
			s:    NewIDSet(1, 2, 3),
			want: 3,
		},
	}
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			if got := tt.s.Size(); got != tt.want {
				t.Errorf("Size() = %v, want %v", got, tt.want)
			}
		})
	}
}

func TestIDSet_Add(t *testing.T) {
	type args struct {
		ids []ID
	}
	type testCase struct {
		name string
		s    IDSet
		args args
	}
	tests := []testCase{
		{
			name: "add multiple",
			s:    NewIDSet(),
			args: args{ids: []ID{1, 2, 3}},
		},
	}
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			tt.s.Add(tt.args.ids...)
			for _, id := range tt.args.ids {
				if !tt.s.Contains(id) {
					t.Errorf("expected set to contain %q", id)
				}
			}
		})
	}
}

func TestIDSet_Remove(t *testing.T) {
	type args struct {
		ids []ID
	}
	type testCase struct {
		name     string
		s        IDSet
		args     args
		expected []ID
	}
	tests := []testCase{
		{
			name:     "remove multiple",
			s:        NewIDSet(1, 2, 3),
			args:     args{ids: []ID{1, 2}},
			expected: []ID{3},
		},
	}
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			tt.s.Remove(tt.args.ids...)
			for _, id := range tt.args.ids {
				if tt.s.Contains(id) {
					t.Errorf("expected set to NOT contain %q", id)
				}
			}
			for _, id := range tt.expected {
				if !tt.s.Contains(id) {
					t.Errorf("expected set to contain %q", id)
				}
			}
		})
	}
}

func TestIDSet_Contains(t *testing.T) {
	type args struct {
		i ID
	}
	type testCase struct {
		name string
		s    IDSet
		args args
		want bool
	}
	tests := []testCase{
		{
			name: "contains",
			s:    NewIDSet(1, 2, 3),
			args: args{i: 1},
			want: true,
		},
		{
			name: "not contains",
			s:    NewIDSet(1, 2, 3),
			args: args{i: 97},
			want: false,
		},
	}
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			if got := tt.s.Contains(tt.args.i); got != tt.want {
				t.Errorf("Contains() = %v, want %v", got, tt.want)
			}
		})
	}
}

func TestIDSet_Clear(t *testing.T) {
	type testCase struct {
		name string
		s    IDSet
	}
	tests := []testCase{
		{
			name: "go case",
			s:    NewIDSet(1, 2, 3),
		},
	}
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			tt.s.Clear()
			assert.Equal(t, 0, tt.s.Size())
		})
	}
}

func TestIDSet_List(t *testing.T) {
	type testCase struct {
		name string
		s    IDSet
		want []ID
	}
	tests := []testCase{
		{
			name: "go case",
			s:    NewIDSet(1, 2, 3),
			want: []ID{1, 2, 3},
		},
	}
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			assert.ElementsMatchf(t, tt.want, tt.s.List(), "List()")
		})
	}
}

func TestIDSet_Sorted(t *testing.T) {
	type testCase struct {
		name string
		s    IDSet
		want []ID
	}
	tests := []testCase{
		{
			name: "go case",
			s:    NewIDSet(1, 2, 3),
			want: []ID{1, 2, 3},
		},
	}
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			assert.Equalf(t, tt.want, tt.s.Sorted(), "Sorted()")
		})
	}
}

func TestIDSet_ContainsAny(t *testing.T) {
	type args struct {
		ids []ID
	}
	type testCase struct {
		name string
		s    IDSet
		args args
		want bool
	}
	tests := []testCase{
		{
			name: "contains one",
			s:    NewIDSet(1, 2, 3),
			args: args{ids: []ID{1, 97}},
			want: true,
		},
		{
			name: "contains all",
			s:    NewIDSet(1, 2, 3),
			args: args{ids: []ID{1, 2}},
			want: true,
		},
		{
			name: "contains none",
			s:    NewIDSet(1, 2, 3),
			args: args{ids: []ID{97, 98}},
			want: false,
		},
	}
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			assert.Equal(t, tt.want, tt.s.ContainsAny(tt.args.ids...), fmt.Sprintf("ContainsAny(%v)", tt.args.ids))
		})
	}
}
// -x-
package file

import (
	"errors"
	"io"
	"os"
)

var _ io.ReadCloser = (*lazyBoundedReadCloser)(nil)
var _ io.ReaderAt = (*lazyBoundedReadCloser)(nil)
var _ io.Seeker = (*lazyBoundedReadCloser)(nil)

// lazyBoundedReadCloser is a "lazy" read closer, allocating a file descriptor for the given path only upon the first Read() call.
// Only part of the file is allowed to be read, starting at a given position.
type lazyBoundedReadCloser struct {
	// path is the path to be opened
	path string
	// file is the active file handle for the given path
	file *os.File
	// reader is the LimitedReader that wraps the open file
	reader *io.SectionReader
	start  int64
	size   int64
}

// NewDeferredPartialReadCloser creates a new NewDeferredPartialReadCloser for the given path.
func newLazyBoundedReadCloser(path string, start, size int64) *lazyBoundedReadCloser {
	return &lazyBoundedReadCloser{
		path:  path,
		start: start,
		size:  size,
	}
}

// Read implements the io.Reader interface for the previously loaded path, opening the file upon the first invocation.
func (d *lazyBoundedReadCloser) Read(b []byte) (int, error) {
	if err := d.openFile(); err != nil {
		return 0, err
	}

	n, err := d.reader.Read(b)
	if err != nil && errors.Is(err, io.EOF) {
		// we've reached the end of the file, force a release of the file descriptor. If the file has already been
		// closed, ignore the error.
		if closeErr := d.file.Close(); !errors.Is(closeErr, os.ErrClosed) {
			return n, closeErr
		}
	}
	return n, err
}

// Close implements the io.Closer interface for the previously loaded path / opened file.
func (d *lazyBoundedReadCloser) Close() error {
	if d.file == nil {
		return nil
	}

	err := d.file.Close()
	if err != nil && errors.Is(err, os.ErrClosed) {
		// ignore the fact that this file has already been closed
		err = nil
	}
	d.file = nil
	d.reader = nil
	return err
}

func (d *lazyBoundedReadCloser) Seek(offset int64, whence int) (int64, error) {
	if err := d.openFile(); err != nil {
		return 0, err
	}

	return d.reader.Seek(offset, whence)
}

func (d *lazyBoundedReadCloser) ReadAt(b []byte, off int64) (n int, err error) {
	if err := d.openFile(); err != nil {
		return 0, err
	}

	n, err = d.reader.ReadAt(b, off)
	if err != nil && errors.Is(err, io.EOF) {
		// we've reached the end of the file, force a release of the file descriptor. If the file has already been
		// closed, ignore the error.
		if closeErr := d.file.Close(); !errors.Is(closeErr, os.ErrClosed) {
			return n, closeErr
		}
	}
	return n, err
}

func (d *lazyBoundedReadCloser) openFile() error {
	if d.reader != nil {
		return nil
	}

	file, err := os.Open(d.path)
	if err != nil {
		return err
	}

	d.file = file
	d.reader = io.NewSectionReader(d.file, d.start, d.size)
	return nil
}
// -x-
package file

import (
	"io"
	"os"
	"testing"

	"github.com/stretchr/testify/require"
)

func getFixture(t *testing.T, filepath string) []byte {
	fh, err := os.Open(filepath)
	require.NoError(t, err)
	expectedContents, err := io.ReadAll(fh)
	require.NoError(t, err)

	return expectedContents
}

func TestDeferredPartialReadCloser(t *testing.T) {
	p := "test-fixtures/a-file.txt"
	contents := getFixture(t, p)

	dReader := newLazyBoundedReadCloser(p, 0, int64(len(contents)))
	require.Nil(t, dReader.file)

	actualContents, err := io.ReadAll(dReader)
	require.NoError(t, err)

	require.Equal(t, contents, actualContents)
	require.NotNil(t, dReader.file)

	require.NoError(t, dReader.Close())
	require.Nil(t, dReader.file, "should not have a file, but we do somehow")
}

func TestDeferredPartialReadCloser_Seek(t *testing.T) {
	p := "test-fixtures/a-file.txt"
	content := getFixture(t, p)

	dReader := newLazyBoundedReadCloser(p, 0, int64(len(content)))
	require.Nil(t, dReader.file)

	var off int64 = 5
	seek, err := dReader.Seek(off, io.SeekStart)
	require.Equal(t, off, seek)
	require.NoError(t, err)
	actualContent, err := io.ReadAll(dReader)
	require.NoError(t, err)

	require.Equal(t, content[int(off):], actualContent)
	require.NotNil(t, dReader.file)

	require.NoError(t, dReader.Close())
	require.Nil(t, dReader.file, "should not have a file, but we do somehow")
}

func TestDeferredPartialReadCloser_PartialRead(t *testing.T) {
	p := "test-fixtures/a-file.txt"
	contents := getFixture(t, p)

	var start, size int64 = 10, 7
	dReader := newLazyBoundedReadCloser(p, start, size)

	actualContents, err := io.ReadAll(dReader)
	require.NoError(t, err)
	require.Equal(t, contents[start:start+size], actualContents)
}
// -x
package file

import (
	"errors"
	"io"
	"os"
)

var _ io.ReadCloser = (*LazyReadCloser)(nil)
var _ io.Seeker = (*LazyReadCloser)(nil)
var _ io.ReaderAt = (*LazyReadCloser)(nil)

// LazyReadCloser is a "lazy" read closer, allocating a file descriptor for the given path only upon the first Read() call.
type LazyReadCloser struct {
	// path is the path to be opened
	path string
	// file is the io.ReadCloser source for the path
	file *os.File
}

// NewLazyReadCloser creates a new LazyReadCloser for the given path.
func NewLazyReadCloser(path string) *LazyReadCloser {
	return &LazyReadCloser{
		path: path,
	}
}

// Read implements the io.Reader interface for the previously loaded path, opening the file upon the first invocation.
func (d *LazyReadCloser) Read(b []byte) (n int, err error) {
	if err := d.openFile(); err != nil {
		return 0, err
	}
	return d.file.Read(b)
}

// Close implements the io.Closer interface for the previously loaded path / opened file.
func (d *LazyReadCloser) Close() error {
	if d.file == nil {
		return nil
	}

	err := d.file.Close()
	if err != nil && errors.Is(err, os.ErrClosed) {
		err = nil
	}
	d.file = nil
	return err
}

func (d *LazyReadCloser) Seek(offset int64, whence int) (int64, error) {
	if err := d.openFile(); err != nil {
		return 0, err
	}

	return d.file.Seek(offset, whence)
}

func (d *LazyReadCloser) ReadAt(p []byte, off int64) (n int, err error) {
	if err := d.openFile(); err != nil {
		return 0, err
	}

	return d.file.ReadAt(p, off)
}

func (d *LazyReadCloser) openFile() error {
	if d.file != nil {
		return nil
	}

	var err error
	d.file, err = os.Open(d.path)
	return err
}
// -x-
package file

import (
	"io"
	"testing"

	"github.com/stretchr/testify/require"
)

func TestDeferredReadCloser(t *testing.T) {
	filepath := "test-fixtures/a-file.txt"
	allContent := getFixture(t, filepath)

	dReader := NewLazyReadCloser(filepath)
	require.Nil(t, dReader.file, "should not have a file, but we do somehow")

	actualContents, err := io.ReadAll(dReader)
	require.NotNil(t, dReader.file, "should have a file, but we do not somehow")
	require.NoError(t, err)
	require.Equal(t, allContent, actualContents)

	require.NoError(t, dReader.Close())
	require.Nil(t, dReader.file, "should not have a file, but we do somehow")
}

func TestLazyReader_ReadAt(t *testing.T) {
	filepath := "test-fixtures/a-file.txt"
	allContent := getFixture(t, filepath)

	dReader := NewLazyReadCloser(filepath)
	require.Nil(t, dReader.file, "should not have a file, but we do somehow")

	off := 5
	left := len(allContent) - off
	s := make([]byte, left)
	n, err := dReader.ReadAt(s, int64(off))
	require.NoError(t, err)
	require.Equal(t, left, n)
	require.Equal(t, allContent[off:], s)

	require.NoError(t, dReader.Close())
	require.Nil(t, dReader.file, "should not have a file, but we do somehow")

}

func TestLazyReader_Seek(t *testing.T) {
	filepath := "test-fixtures/a-file.txt"
	allContent := getFixture(t, filepath)

	dReader := NewLazyReadCloser(filepath)
	require.Nil(t, dReader.file, "should not have a file, but we do somehow")

	off := 5
	left := len(allContent) - off
	s := make([]byte, left)
	seek, err := dReader.Seek(int64(off), io.SeekStart)
	require.NoError(t, err)
	require.Equal(t, seek, int64(off))

	n, err := dReader.Read(s)
	require.NoError(t, err)
	require.Equal(t, left, n)
	require.Equal(t, allContent[off:], s)

	require.NoError(t, dReader.Close())
	require.Nil(t, dReader.file, "should not have a file, but we do somehow")
}
// -x-
package file

import (
	"archive/tar"
	"io"
	"io/fs"
	"os"
	"path"
	"path/filepath"
	"time"

	"github.com/sylabs/squashfs"

	"github.com/anchore/stereoscope/internal/log"
)

var _ fs.FileInfo = (*ManualInfo)(nil)

// Metadata represents all file metadata of interest.
type Metadata struct {
	fs.FileInfo

	// Path is the absolute path representation to the file
	Path string
	// LinkDestination is populated only for hardlinks / symlinks, can be an absolute or relative
	LinkDestination string
	UserID          int
	GroupID         int
	Type            Type
	MIMEType        string
}

type ManualInfo struct {
	NameValue    string
	SizeValue    int64
	ModeValue    fs.FileMode
	ModTimeValue time.Time
	SysValue     any
}

func (m ManualInfo) Name() string {
	return m.NameValue
}

func (m ManualInfo) Size() int64 {
	return m.SizeValue
}

func (m ManualInfo) Mode() fs.FileMode {
	return m.ModeValue
}

func (m ManualInfo) ModTime() time.Time {
	return m.ModTimeValue
}

func (m ManualInfo) IsDir() bool {
	return m.ModeValue.IsDir()
}

func (m ManualInfo) Sys() any {
	return m.SysValue
}

func NewMetadata(header tar.Header, content io.Reader) Metadata {
	return Metadata{
		FileInfo:        header.FileInfo(),
		Path:            path.Clean(DirSeparator + header.Name),
		Type:            TypeFromTarType(header.Typeflag),
		LinkDestination: header.Linkname,
		UserID:          header.Uid,
		GroupID:         header.Gid,
		MIMEType:        MIMEType(content),
	}
}

// NewMetadataFromSquashFSFile populates Metadata for the entry at path, with details from f.
func NewMetadataFromSquashFSFile(path string, f *squashfs.File) (Metadata, error) {
	fi, err := f.Stat()
	if err != nil {
		return Metadata{}, err
	}

	var ty Type
	switch {
	case fi.IsDir():
		ty = TypeDirectory
	case f.IsRegular():
		ty = TypeRegular
	case f.IsSymlink():
		ty = TypeSymLink
	default:
		switch fi.Mode() & os.ModeType {
		case os.ModeNamedPipe:
			ty = TypeFIFO
		case os.ModeSocket:
			ty = TypeSocket
		case os.ModeDevice:
			ty = TypeBlockDevice
		case os.ModeCharDevice:
			ty = TypeCharacterDevice
		case os.ModeIrregular:
			ty = TypeIrregular
		}
		// note: cannot determine hardlink from squashfs.File (but case us not possible)
	}

	md := Metadata{
		FileInfo:        fi,
		Path:            filepath.Clean(filepath.Join("/", path)),
		LinkDestination: f.SymlinkPath(),
		UserID:          -1,
		GroupID:         -1,
		Type:            ty,
	}

	if f.IsRegular() {
		md.MIMEType = MIMEType(f)
	}

	return md, nil
}

func NewMetadataFromPath(path string, info os.FileInfo) Metadata {
	var mimeType string
	uid, gid := getXid(info)

	ty := TypeFromMode(info.Mode())

	if ty == TypeRegular {
		f, err := os.Open(path)
		if err != nil {
			// TODO: it may be that the file is inaccessible, however, this is not an error or a warning. In the future we need to track these as known-unknowns
			f = nil
		} else {
			defer func() {
				if err := f.Close(); err != nil {
					log.Warnf("unable to close file while obtaining metadata: %s", path)
				}
			}()
		}

		mimeType = MIMEType(f)
	}

	return Metadata{
		FileInfo: info,
		Path:     path,
		Type:     ty,
		// unsupported across platforms
		UserID:   uid,
		GroupID:  gid,
		MIMEType: mimeType,
	}
}

func (m Metadata) Equal(other Metadata) bool {
	return m.Path == other.Path &&
		m.LinkDestination == other.LinkDestination &&
		m.UserID == other.UserID &&
		m.GroupID == other.GroupID &&
		m.Type == other.Type &&
		m.MIMEType == other.MIMEType &&
		m.FileInfo.Name() == other.FileInfo.Name() &&
		m.FileInfo.IsDir() == other.FileInfo.IsDir() &&
		m.FileInfo.Mode() == other.FileInfo.Mode() &&
		m.FileInfo.Size() == other.FileInfo.Size() &&
		m.FileInfo.ModTime().UTC().Equal(other.FileInfo.ModTime().UTC())
}
// -x-
package file

import (
	"io"
	"strings"

	"github.com/gabriel-vasile/mimetype"
)

// MIMEType attempts to guess at the MIME type of a file given the contents. If there is no contents, then an empty
// string is returned. If the MIME type could not be determined and the contents are not empty, then a MIME type
// of "application/octet-stream" is returned.
func MIMEType(reader io.Reader) string {
	if reader == nil {
		return ""
	}

	s := sizer{reader: reader}

	var mTypeStr string
	mType, err := mimetype.DetectReader(&s)
	if err == nil {
		// extract the string mimetype and ignore aux information (e.g. 'text/plain; charset=utf-8' -> 'text/plain')
		mTypeStr = strings.Split(mType.String(), ";")[0]
	}

	// we may have a reader that is not nil but the observed contents was empty
	if s.size == 0 {
		return ""
	}

	return mTypeStr
}

type sizer struct {
	reader io.Reader
	size   int64
}

func (s *sizer) Read(p []byte) (int, error) {
	n, err := s.reader.Read(p)
	s.size += int64(n)
	return n, err
}
// -x-
package file

import (
	"fmt"
	"path"
	"strings"
)

const (
	WhiteoutPrefix = ".wh."
	OpaqueWhiteout = WhiteoutPrefix + WhiteoutPrefix + ".opq"
	DirSeparator   = "/"
)

// Path represents a file path
type Path string

// Normalize returns the cleaned file path representation (trimmed of spaces and resolve relative notations)
func (p Path) Normalize() Path {
	// note: when normalizing we cannot trim trailing whitespace since it is valid for a path to have suffix whitespace
	var trimmed = string(p)
	if strings.Count(trimmed, " ") < len(trimmed) {
		trimmed = strings.TrimLeft(string(p), " ")
	}

	// remove trailing dir separators
	trimmed = strings.TrimRight(trimmed, DirSeparator)

	// special case for root "/"
	if trimmed == "" {
		return DirSeparator
	}
	return Path(path.Clean(trimmed))
}

func (p Path) IsAbsolutePath() bool {
	return strings.HasPrefix(string(p), DirSeparator)
}

// Basename of the path (i.e. filename)
func (p Path) Basename() string {
	return path.Base(string(p))
}

// IsDirWhiteout indicates if the path has a basename is a opaque whiteout (which means all parent directory contents should be ignored during squashing)
func (p Path) IsDirWhiteout() bool {
	return p.Basename() == OpaqueWhiteout
}

// IsWhiteout indicates if the file basename has a whiteout prefix (which means that the file should be removed during squashing)
func (p Path) IsWhiteout() bool {
	return strings.HasPrefix(p.Basename(), WhiteoutPrefix)
}

// UnWhiteoutPath is a representation of the current path with no whiteout prefixes
func (p Path) UnWhiteoutPath() (Path, error) {
	basename := p.Basename()
	if strings.HasPrefix(basename, OpaqueWhiteout) {
		return p.ParentPath()
	}
	parent, err := p.ParentPath()
	if err != nil {
		return "", err
	}
	return Path(path.Join(string(parent), strings.TrimPrefix(basename, WhiteoutPrefix))), nil
}

// ParentPath returns a path object to the current files parent directory (or errors out if there is no parent)
func (p Path) ParentPath() (Path, error) {
	parent, child := path.Split(string(p))
	sanitized := Path(parent).Normalize()
	if sanitized == "/" {
		if child != "" {
			return "/", nil
		}
		return "", fmt.Errorf("no parent")
	}
	return sanitized, nil
}

// AllPaths returns all constituent paths of the current path + the current path itself (e.g. /home/wagoodman/file.txt -> /, /home, /home/wagoodman, /home/wagoodman/file.txt )
func (p Path) AllPaths() []Path {
	fullPaths := p.ConstituentPaths()
	if p != "/" {
		fullPaths = append(fullPaths, p)
	}
	return fullPaths
}

// ConstituentPaths returns all constituent paths for the current path (not including the current path itself) (e.g. /home/wagoodman/file.txt -> /, /home, /home/wagoodman )
func (p Path) ConstituentPaths() []Path {
	parents := strings.Split(strings.Trim(string(p), DirSeparator), DirSeparator)
	fullPaths := make([]Path, len(parents))
	for idx := range parents {
		cur := DirSeparator + strings.Join(parents[:idx], DirSeparator)
		fullPaths[idx] = Path(cur)
	}
	return fullPaths
}

type Paths []Path

func (p Paths) Len() int           { return len(p) }
func (p Paths) Swap(i, j int)      { p[i], p[j] = p[j], p[i] }
func (p Paths) Less(i, j int) bool { return string(p[i]) < string(p[j]) }
// -x-
//nolint:dupl
package file

import (
	"sort"
)

type PathSet map[Path]struct{}

func NewPathSet(is ...Path) PathSet {
	// TODO: replace with single generic implementation that also incorporates other set implementations
	s := make(PathSet)
	s.Add(is...)
	return s
}

func (s PathSet) Size() int {
	return len(s)
}

func (s PathSet) Merge(other PathSet) {
	for _, i := range other.List() {
		s.Add(i)
	}
}

func (s PathSet) Add(ids ...Path) {
	for _, i := range ids {
		s[i] = struct{}{}
	}
}

func (s PathSet) Remove(ids ...Path) {
	for _, i := range ids {
		delete(s, i)
	}
}

func (s PathSet) Contains(i Path) bool {
	_, ok := s[i]
	return ok
}

func (s PathSet) Clear() {
	// TODO: replace this with the new 'clear' keyword when it's available in go 1.20 or 1.21
	for i := range s {
		delete(s, i)
	}
}

func (s PathSet) List() []Path {
	ret := make([]Path, 0, len(s))
	for i := range s {
		ret = append(ret, i)
	}
	return ret
}

func (s PathSet) Sorted() []Path {
	ids := s.List()

	sort.Slice(ids, func(i, j int) bool {
		return ids[i] < ids[j]
	})

	return ids
}

func (s PathSet) ContainsAny(ids ...Path) bool {
	for _, i := range ids {
		_, ok := s[i]
		if ok {
			return true
		}
	}
	return false
}

type PathCountSet map[Path]int

func NewPathCountSet(is ...Path) PathCountSet {
	s := make(PathCountSet)
	s.Add(is...)
	return s
}

func (s PathCountSet) Add(ids ...Path) {
	for _, i := range ids {
		if _, ok := s[i]; !ok {
			s[i] = 1
			continue
		}
		s[i]++
	}
}

func (s PathCountSet) Remove(ids ...Path) {
	for _, i := range ids {
		if _, ok := s[i]; !ok {
			continue
		}

		s[i]--
		if s[i] <= 0 {
			delete(s, i)
		}
	}
}

func (s PathCountSet) Contains(i Path) bool {
	count, ok := s[i]
	return ok && count > 0
}
// -x-
package file

type PathStack []Path

func (s *PathStack) Size() int {
	return len(*s)
}

func (s *PathStack) Pop() Path {
	v := *s
	v, n := v[:len(v)-1], v[len(v)-1]
	*s = v
	return n
}

func (s *PathStack) Push(n Path) {
	*s = append(*s, n)
}
// -x-
package file

import "fmt"

// Reference represents a unique file. This is useful when path is not good enough (i.e. you have the same file path for two files in two different container image layers, and you need to be able to distinguish them apart)
type Reference struct {
	id       ID
	RealPath Path // file path with NO symlinks or hardlinks in constituent paths
}

// NewFileReference creates a new unique file reference for the given path.
func NewFileReference(path Path) *Reference {
	return &Reference{
		RealPath: path,
		id:       ID(nextID.Add(1)),
	}
}

// ID returns the unique ID for this file reference.
func (f *Reference) ID() ID {
	return f.id
}

// String returns a string representation of the path with a unique ID.
func (f *Reference) String() string {
	if f == nil {
		return "[nil]"
	}
	return fmt.Sprintf("[%v] real=%q", f.id, f.RealPath)
}
// -x-
package file

// References is a slice of file references (useful for attaching sorting-related methods)
type References []*Reference

func (f References) Len() int {
	return len(f)
}

func (f References) Swap(idx1, idx2 int) {
	f[idx1], f[idx2] = f[idx2], f[idx1]
}

func (f References) Less(idx1, idx2 int) bool {
	return f[idx1].RealPath < f[idx2].RealPath
}

func (f References) Equal(other References) bool {
	if len(f) != len(other) {
		return false
	}
	for i, v := range f {
		if v != other[i] {
			return false
		}
	}
	return true
}
// -x-
package file

import (
	"sort"

	"github.com/scylladb/go-set/strset"
)

// Resolution represents the fetching of a possibly non-existent file via a request path.
type Resolution struct {
	RequestPath Path
	*Reference
	// LinkResolutions represents the traversal through the filesystem to access to current reference, including all symlink and hardlink resolution.
	// note: today this only shows resolutions via the basename of the request path, but in the future it may show all resolutions.
	LinkResolutions []Resolution
}

type Resolutions []Resolution

// NewResolution create a new Resolution for the given request path, showing the resolved reference (or
// nil if it does not exist), and the link resolution of the basename of the request path transitively.
func NewResolution(path Path, ref *Reference, leafs []Resolution) *Resolution {
	return &Resolution{
		RequestPath:     path,
		Reference:       ref,
		LinkResolutions: leafs,
	}
}

func (f Resolutions) Len() int {
	return len(f)
}

func (f Resolutions) Less(i, j int) bool {
	ith := f[i]
	jth := f[j]

	ithIsReal := ith.Reference != nil && ith.Reference.RealPath == ith.RequestPath
	jthIsReal := jth.Reference != nil && jth.Reference.RealPath == jth.RequestPath

	switch {
	case ithIsReal && !jthIsReal:
		return true
	case !ithIsReal && jthIsReal:
		return false
	}

	return ith.RequestPath < jth.RequestPath
}

func (f Resolutions) Swap(i, j int) {
	f[i], f[j] = f[j], f[i]
}

func (f *Resolution) HasReference() bool {
	if f == nil {
		return false
	}
	return f.Reference != nil
}

func (f *Resolution) AllPaths() []Path {
	set := strset.New()
	set.Add(string(f.RequestPath))
	if f.Reference != nil {
		set.Add(string(f.Reference.RealPath))
	}
	for _, p := range f.LinkResolutions {
		set.Add(string(p.RequestPath))
		if p.Reference != nil {
			set.Add(string(p.Reference.RealPath))
		}
	}

	paths := set.List()
	sort.Strings(paths)

	var results []Path
	for _, p := range paths {
		results = append(results, Path(p))
	}
	return results
}

func (f *Resolution) AllRequestPaths() []Path {
	set := strset.New()
	set.Add(string(f.RequestPath))
	for _, p := range f.LinkResolutions {
		set.Add(string(p.RequestPath))
	}

	paths := set.List()
	sort.Strings(paths)

	var results []Path
	for _, p := range paths {
		results = append(results, Path(p))
	}
	return results
}

// RequestResolutionPath represents the traversal through the filesystem to access to current reference, including all symlink and hardlink resolution.
func (f *Resolution) RequestResolutionPath() []Path {
	var paths []Path
	var firstPath Path
	var lastLinkResolutionIsDead bool

	if string(f.RequestPath) != "" {
		firstPath = f.RequestPath
		paths = append(paths, f.RequestPath)
	}
	for i, p := range f.LinkResolutions {
		if i == 0 && p.RequestPath == f.RequestPath {
			// ignore link resolution that starts with the same user requested path
			continue
		}
		if firstPath == "" {
			firstPath = p.RequestPath
		}

		paths = append(paths, p.RequestPath)

		if i == len(f.LinkResolutions)-1 {
			// we've reached the final link resolution
			if p.Reference == nil {
				lastLinkResolutionIsDead = true
			}
		}
	}
	if f.HasReference() && firstPath != f.Reference.RealPath && !lastLinkResolutionIsDead {
		// we've reached the final reference that was resolved
		// we should only do this if there was a link resolution
		paths = append(paths, f.Reference.RealPath)
	}
	return paths
}

// References represents the traversal through the filesystem to access to current reference, including all symlink and hardlink resolution.
func (f *Resolution) References() []Reference {
	var refs []Reference
	var lastLinkResolutionIsDead bool

	for i, p := range f.LinkResolutions {
		if p.Reference != nil {
			refs = append(refs, *p.Reference)
		}
		if i == len(f.LinkResolutions)-1 {
			// we've reached the final link resolution
			if p.Reference == nil {
				lastLinkResolutionIsDead = true
			}
		}
	}
	if f.Reference != nil && !lastLinkResolutionIsDead {
		refs = append(refs, *f.Reference)
	}
	return refs
}
// -x-