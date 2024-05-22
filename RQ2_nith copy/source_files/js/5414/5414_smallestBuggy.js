{prepend_content}
function asset_request(req, callback) {
  var filename = path.join(__dirname, "public", req.url.path_list.join("/"));
  fs.access(filename, function(fs_err) {
    if (!fs_err) {
      fs.readFile(filename, function(err, data) {
        callback({
          body: data,
          type: mime.getType(filename),
          err: err,
        });
      });
    } else {
      callback({
        body: "Not found",
        status: -2,
        code: 404,
      });
    }
  });
}
{append_content}