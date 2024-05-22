// -x-
var helpers = require("../helpers");
var config = require("../../config");
var skins = require("../skins");
var cache = require("../cache");
var path = require("path");
var url = require("url");
// -x-
// handle the appropriate 'default=' response
// uses either mhf_steve or mhf_alex (based on +userId+) if no +def+ given
// callback: response object
function handle_default(img_status, userId, size, def, req, err, callback) {
  def = def || skins.default_skin(userId);
  var defname = def.toLowerCase();
  if (defname !== "steve" && defname !== "mhf_steve" && defname !== "alex" && defname !== "mhf_alex") {
    if (helpers.id_valid(def)) {
      // clean up the old URL to match new image
      req.url.searchParams.delete('default');
      req.url.path_list[1] = def;
      req.url.pathname = req.url.path_list.join('/');
      var newUrl = req.url.toString();
      callback({
        status: img_status,
        redirect: newUrl,
        err: err,
      });
    } else {
      callback({
        status: img_status,
        redirect: def,
        err: err,
      });
    }
  } else {
    // handle steve and alex
    def = defname;
    if (def.substr(0, 4) !== "mhf_") {
      def = "mhf_" + def;
    }
    skins.resize_img(path.join(__dirname, "..", "public", "images", def + ".png"), size, function(resize_err, image) {
      callback({
        status: img_status,
        body: image,
        type: "image/png",
        hash: def,
        err: resize_err || err,
      });
    });
  }
}
// -x-
// GET avatar request
module.exports = function(req, callback) {
  var userId = (req.url.path_list[1] || "").split(".")[0];
  var size = parseInt(req.url.searchParams.get("size")) || config.avatars.default_size;
  var def = req.url.searchParams.get("default");
  var overlay = req.url.searchParams.has("overlay") || req.url.searchParams.has("helm");

  // check for extra paths
  if (req.url.path_list.length > 2) {
    callback({
      status: -2,
      body: "Invalid Path",
      code: 404,
    });
    return;
  }

  // strip dashes
  userId = userId.replace(/-/g, "");

  // Prevent app from crashing/freezing
  if (size < config.avatars.min_size || size > config.avatars.max_size) {
    // "Unprocessable Entity", valid request, but semantically erroneous:
    // https://tools.ietf.org/html/rfc4918#page-78
    callback({
      status: -2,
      body: "Invalid Size",
    });
    return;
  } else if (!helpers.id_valid(userId)) {
    callback({
      status: -2,
      body: "Invalid UUID",
    });
    return;
  }

  try {
    helpers.get_avatar(req.id, userId, overlay, size, function(err, status, image, hash) {
      if (err) {
        if (err.code === "ENOENT") {
          // no such file
          cache.remove_hash(req.id, userId);
        }
      }
      if (image) {
        callback({
          status: status,
          body: image,
          type: "image/png",
          err: err,
          hash: hash,
        });
      } else {
        handle_default(status, userId, size, def, req, err, callback);
      }
    });
  } catch (e) {
    handle_default(-1, userId, size, def, req, e, callback);
  }
};
// -x-
var helpers = require("../helpers");
var cache = require("../cache");
// -x-
// GET cape request
module.exports = function(req, callback) {
  var userId = (req.url.path_list[1] || "").split(".")[0];
  var def = req.url.searchParams.get('default');
  var rid = req.id;

  // check for extra paths
  if (req.url.path_list.length > 2) {
    callback({
      status: -2,
      body: "Invalid Path",
      code: 404
    });
    return;
  }

  // strip dashes
  userId = userId.replace(/-/g, "");
  if (!helpers.id_valid(userId)) {
    callback({
      status: -2,
      body: "Invalid UUID"
    });
    return;
  }

  try {
    helpers.get_cape(rid, userId, function(err, hash, status, image) {
      if (err) {
        if (err.code === "ENOENT") {
          // no such file
          cache.remove_hash(rid, userId);
        }
      }
      callback({
        status: status,
        body: image,
        type: image ? "image/png" : undefined,
        redirect: image ? undefined : def,
        hash: hash,
        err: err
      });
    });
  } catch(e) {
    callback({
      status: -1,
      err: e
    });
  }
};
// -x-
var logging = require("../logging");
var config = require("../../config");
var path = require("path");
var read = require("fs").readFileSync;
var ejs = require("ejs");

var str;
var index;
// -x-
// pre-compile the index page
function compile() {
  logging.log("Compiling index page");
  str = read(path.join(__dirname, "..", "views", "index.html.ejs"), "utf-8");
  index = ejs.compile(str);
}
// -x-
compile();
// -x-
// GET index request
module.exports = function(req, callback) {
  if (config.server.debug_enabled) {
    // allow changes without reloading
    compile();
  }
  var html = index({
    title: "Crafatar",
    domain: "https://" + req.headers.host,
    config: config
  });
  callback({
    body: html,
    type: "text/html; charset=utf-8"
  });
};
// -x-
var logging = require("../logging");
var helpers = require("../helpers");
var renders = require("../renders");
var config = require("../../config");
var cache = require("../cache");
var skins = require("../skins");
var path = require("path");
var url = require("url");
var fs = require("fs");
// -x-
// handle the appropriate 'default=' response
// uses either mhf_steve or mhf_alex (based on +userId+) if no +def+ given
// callback: response object
function handle_default(rid, scale, overlay, body, img_status, userId, size, def, req, err, callback) {
  def = def || skins.default_skin(userId);
  var defname = def.toLowerCase();
  if (defname !== "steve" && defname !== "mhf_steve" && defname !== "alex" && defname !== "mhf_alex") {
    if (helpers.id_valid(def)) {
      // clean up the old URL to match new image
      req.url.searchParams.delete('default');
      req.url.path_list[2] = def;
      req.url.pathname = req.url.path_list.join('/');
      var newUrl = req.url.toString();
      callback({
        status: img_status,
        redirect: newUrl,
        err: err
      });
    } else {
      callback({
        status: img_status,
        redirect: def,
        err: err
      });
    }
  } else {
    // handle steve and alex
    def = defname;
    if (def.substr(0, 4) !== "mhf_") {
      def = "mhf_" + def;
    }
    fs.readFile(path.join(__dirname, "..", "public", "images", def + "_skin.png"), function(fs_err, buf) {
      // we render the default skins, but not custom images
      renders.draw_model(rid, buf, scale, overlay, body, def === "mhf_alex", function(render_err, def_img) {
        callback({
          status: img_status,
          body: def_img,
          type: "image/png",
          hash: def,
          err: render_err || fs_err || err
        });
      });
    });
  }
}
// -x-
// GET render request
module.exports = function(req, callback) {
  var raw_type = req.url.path_list[1] || "";
  var rid = req.id;
  var body = raw_type === "body";
  var userId = (req.url.path_list[2] || "").split(".")[0];
  var def = req.url.searchParams.get("default");
  var scale = parseInt(req.url.searchParams.get("scale")) || config.renders.default_scale;
  var overlay = req.url.searchParams.has("overlay") || req.url.searchParams.has("helm");

  // check for extra paths
  if (req.url.path_list.length > 3) {
    callback({
      status: -2,
      body: "Invalid Path",
      code: 404
    });
    return;
  }

  // validate type
  if (raw_type !== "body" && raw_type !== "head") {
    callback({
      status: -2,
      body: "Invalid Render Type"
    });
    return;
  }

  // strip dashes
  userId = userId.replace(/-/g, "");

  if (scale < config.renders.min_scale || scale > config.renders.max_scale) {
    callback({
      status: -2,
      body: "Invalid Scale"
    });
    return;
  } else if (!helpers.id_valid(userId)) {
    callback({
      status: -2,
      body: "Invalid UUID"
    });
    return;
  }

  try {
    helpers.get_render(rid, userId, scale, overlay, body, function(err, status, hash, image) {
      if (err) {
        if (err.code === "ENOENT") {
          // no such file
          cache.remove_hash(rid, userId);
        }
      }
      if (image) {
        callback({
          status: status,
          body: image,
          type: "image/png",
          hash: hash,
          err: err
        });
      } else {
        logging.debug(rid, "image not found, using default.");
        handle_default(rid, scale, overlay, body, status, userId, scale, def, req, err, callback);
      }
    });
  } catch(e) {
    handle_default(rid, scale, overlay, body, -1, userId, scale, def, req, e, callback);
  }
};
// -x-
var helpers = require("../helpers");
var skins = require("../skins");
var cache = require("../cache");
var path = require("path");
var lwip = require("@randy.tarampi/lwip");
var url = require("url");
// -x-
// handle the appropriate 'default=' response
// uses either mhf_steve or mhf_alex (based on +userId+) if no +def+ given
// callback: response object
function handle_default(img_status, userId, def, req, err, callback) {
  def = def || skins.default_skin(userId);
  var defname = def.toLowerCase();
  if (defname !== "steve" && defname !== "mhf_steve" && defname !== "alex" && defname !== "mhf_alex") {
    if (helpers.id_valid(def)) {
      // clean up the old URL to match new image
      req.url.searchParams.delete('default');
      req.url.path_list[1] = def;
      req.url.pathname = req.url.path_list.join('/');
      var newUrl = req.url.toString();
      callback({
        status: img_status,
        redirect: newUrl,
        err: err
      });
    } else {
      callback({
        status: img_status,
        redirect: def,
        err: err
      });
    }
  } else {
    // handle steve and alex
    def = defname;
    if (def.substr(0, 4) !== "mhf_") {
      def = "mhf_" + def;
    }
    lwip.open(path.join(__dirname, "..", "public", "images", def + "_skin.png"), function(lwip_err, image) {
      if (image) {
        image.toBuffer("png", function(buf_err, buffer) {
          callback({
            status: img_status,
            body: buffer,
            type: "image/png",
            hash: def,
            err: buf_err || lwip_err || err
          });
        });
      } else {
        callback({
          status: -1,
          err: lwip_err || err
        });
      }
    });
  }
}
// -x-
// GET skin request
module.exports = function(req, callback) {
  var userId = (req.url.path_list[1] || "").split(".")[0];
  var def = req.url.searchParams.get("default");
  var rid = req.id;

  // check for extra paths
  if (req.url.path_list.length > 2) {
    callback({
      status: -2,
      body: "Invalid Path",
      code: 404
    });
    return;
  }

  // strip dashes
  userId = userId.replace(/-/g, "");
  if (!helpers.id_valid(userId)) {
    callback({
      status: -2,
      body: "Invalid UUID"
    });
    return;
  }

  try {
    helpers.get_skin(rid, userId, function(err, hash, status, image, slim) {
      if (err) {
        if (err.code === "ENOENT") {
          // no such file
          cache.remove_hash(req.id, userId);
        }
      }
      if (image) {
        callback({
          status: status,
          body: image,
          type: "image/png",
          hash: hash,
          err: err
        });
      } else {
        handle_default(2, userId, def, req, err, callback);
      }
    });
  } catch(e) {
    handle_default(-1, userId, def, req, e, callback);
  }
};
// -x-
var logging = require("./logging");
var node_redis = require("redis");
var config = require("../config");

var redis = null;
// -x-
// sets up redis connection
// flushes redis when using ephemeral storage (e.g. Heroku)
function connect_redis() {
  logging.log("connecting to redis...");
  redis = node_redis.createClient(config.redis);
  redis.on("ready", function() {
    logging.log("Redis connection established.");
    if (config.caching.ephemeral) {
      logging.log("Storage is ephemeral, flushing redis");
      redis.flushall();
    }
  });
  redis.on("error", function(err) {
    logging.error(err);
  });
  redis.on("end", function() {
    logging.warn("Redis connection lost!");
  });
}
// -x-
var exp = {};
// -x-
// returns the redis instance
exp.get_redis = function() {
  return redis;
};
// -x-
// set model type to value of *slim*
exp.set_slim = function(rid, userId, slim, callback) {
  logging.debug(rid, "setting slim for", userId, "to " + slim);
  // store userId in lower case if not null
  userId = userId && userId.toLowerCase();

  redis.hmset(userId, ["a", Number(slim)], callback);
};
// -x-
// sets the timestamp for +userId+
// if +temp+ is true, the timestamp is set so that the record will be outdated after 60 seconds
// these 60 seconds match the duration of Mojang's rate limit ban
// callback: error
exp.update_timestamp = function(rid, userId, temp, callback) {
  logging.debug(rid, "updating cache timestamp (" + temp + ")");
  var sub = temp ? config.caching.local - 60 : 0;
  var time = Date.now() - sub;
  // store userId in lower case if not null
  userId = userId && userId.toLowerCase();
  redis.hmset(userId, "t", time, function(err) {
    callback(err);
  });
};
// -x-
// create the key +userId+, store +skin_hash+, +cape_hash+, +slim+ and current time
// if +skin_hash+ or +cape_hash+ are undefined, they aren't stored
// this is useful to store cape and skin at separate times, without overwriting the other
// +slim+ can be true (alex) or false (steve)
// +callback+ contans error
exp.save_hash = function(rid, userId, skin_hash, cape_hash, slim, callback) {
  logging.debug(rid, "caching skin:" + skin_hash + " cape:" + cape_hash + " slim:" + slim);
  // store shorter null value instead of "null" string
  skin_hash = skin_hash === null ? "" : skin_hash;
  cape_hash = cape_hash === null ? "" : cape_hash;
  // store userId in lower case if not null
  userId = userId && userId.toLowerCase();

  var args = [];
  if (cape_hash !== undefined) {
    args.push("c", cape_hash);
  }
  if (skin_hash !== undefined) {
    args.push("s", skin_hash);
  }
  if (slim !== undefined) {
    args.push("a", Number(!!slim));
  }
  args.push("t", Date.now());

  redis.hmset(userId, args, function(err) {
    callback(err);
  });
};
// -x-
// removes the hash for +userId+ from the cache
exp.remove_hash = function(rid, userId) {
  logging.debug(rid, "deleting hash from cache");
  redis.del(userId.toLowerCase(), "h", "t");
};
// -x-
// get a details object for +userId+
// {skin: "0123456789abcdef", cape: "gs1gds1g5d1g5ds1", time: 1414881524512}
// callback: error, details
// details is null when userId not cached
exp.get_details = function(userId, callback) {
  // get userId in lower case if not null
  userId = userId && userId.toLowerCase();
  redis.hgetall(userId, function(err, data) {
    var details = null;
    if (data) {
      details = {
        skin: data.s === "" ? null : data.s,
        cape: data.c === "" ? null : data.c,
        slim: data.a === "1",
        time: Number(data.t)
      };
    }
    callback(err, details);
  });
};
// -x-
connect_redis();
module.exports = exp;
// -x-
var networking = require("./networking");
var logging = require("./logging");
var renders = require("./renders");
var config = require("../config");
var cache = require("./cache");
var skins = require("./skins");
var path = require("path");
var fs = require("fs");
// -x-
// 0098cb60fa8e427cb299793cbd302c9a
var valid_user_id = /^[0-9a-fA-F]{32}$/; // uuid
var hash_pattern = /[0-9a-f]+$/;
// -x-
// gets the hash from the textures.minecraft.net +url+
function get_hash(url) {
  return hash_pattern.exec(url)[0].toLowerCase();
}
// -x-
// gets the skin for +userId+ with +profile+
// uses +cache_details+ to determine if the skin needs to be downloaded or can be taken from cache
// face and face+helm images are extracted and stored to files
// callback: error, skin hash, slim
function store_skin(rid, userId, profile, cache_details, callback) {
  networking.get_skin_info(rid, userId, profile, function(err, url, slim) {
    if (err) {
      slim = cache_details ? cache_details.slim : undefined;
    }

    if (!err && url) {
      var skin_hash = get_hash(url);
      if (cache_details && cache_details.skin === skin_hash) {
        cache.update_timestamp(rid, userId, false, function(cache_err) {
          callback(cache_err, skin_hash, slim);
        });
      } else {
        logging.debug(rid, "new skin hash:", skin_hash);
        var facepath = path.join(config.directories.faces, skin_hash + ".png");
        var helmpath = path.join(config.directories.helms, skin_hash + ".png");
        var skinpath = path.join(config.directories.skins, skin_hash + ".png");
        fs.access(facepath, function(fs_err) {
          if (!fs_err) {
            logging.debug(rid, "skin already exists, not downloading");
            callback(null, skin_hash, slim);
          } else {
            networking.get_from(rid, url, function(img, response, err1) {
              if (err1 || !img) {
                callback(err1, null, slim);
              } else {
                skins.save_image(img, skinpath, function(skin_err) {
                  if (skin_err) {
                    callback(skin_err, null, slim);
                  } else {
                    skins.extract_face(img, facepath, function(err2) {
                      if (err2) {
                        callback(err2, null, slim);
                      } else {
                        logging.debug(rid, "face extracted");
                        skins.extract_helm(rid, facepath, img, helmpath, function(err3) {
                          logging.debug(rid, "helm extracted");
                          logging.debug(rid, helmpath);
                          callback(err3, skin_hash, slim);
                        });
                      }
                    });
                  }
                });
              }
            });
          }
        });
      }
    } else {
      callback(err, null);
    }
  });
}
// -x-
// gets the cape for +userId+ with +profile+
// uses +cache_details+ to determine if the cape needs to be downloaded or can be taken from cache
// the cape - if downloaded - is stored to file
// callback: error, cape hash
function store_cape(rid, userId, profile, cache_details, callback) {
  networking.get_cape_url(rid, userId, profile, function(err, url) {
    if (!err && url) {
      var cape_hash = get_hash(url);
      if (cache_details && cache_details.cape === cape_hash) {
        cache.update_timestamp(rid, userId, false, function(cache_err) {
          callback(cache_err, cape_hash);
        });
      } else {
        logging.debug(rid, "new cape hash:", cape_hash);
        var capepath = path.join(config.directories.capes, cape_hash + ".png");
        fs.access(capepath, function(fs_err) {
          if (!fs_err) {
            logging.debug(rid, "cape already exists, not downloading");
            callback(null, cape_hash);
          } else {
            networking.get_from(rid, url, function(img, response, net_err) {
              if (net_err || !img) {
                callback(net_err, null);
              } else {
                skins.save_image(img, capepath, function(skin_err) {
                  logging.debug(rid, "cape saved");
                  callback(skin_err, cape_hash);
                });
              }
            });
          }
        });
      }
    } else {
      callback(err, null);
    }
  });
}
// -x-
// used by store_images to queue simultaneous requests for identical userId
// the first request has to be completed until all others are continued
// otherwise we risk running into Mojang's rate limit and deleting the cached skin
var requests = {
  skin: {},
  cape: {}
};
// -x-
var loginterval = setInterval(function(){
  var skinreqs = Object.keys(requests.skin).length;
  var capereqs = Object.keys(requests.cape).length;
  if (skinreqs || capereqs) {
    logging.log("Currently waiting for " + skinreqs + " skin requests and " + capereqs + " cape requests.");
  }
}, 1000);
// -x-
// add a request for +userId+ and +type+ to the queue
function push_request(userId, type, callback) {
  // avoid special properties (e.g. 'constructor')
  var userId_safe = "!" + userId;
  if (!requests[type][userId_safe]) {
    requests[type][userId_safe] = [];
  }
  requests[type][userId_safe].push(callback);
}
// -x-
// calls back all queued requests that match userId and type
function resume(userId, type, err, hash, slim) {
  var userId_safe = "!" + userId;
  var callbacks = requests[type][userId_safe];
  if (callbacks) {
    if (callbacks.length > 1) {
      logging.debug(callbacks.length, "simultaneous requests for", userId);
    }

    for (var i = 0; i < callbacks.length; i++) {
      // continue the request
      callbacks[i](err, hash, slim);
      // remove from array
      callbacks.splice(i, 1);
      i--;
    }

    // it's still an empty array
    delete requests[type][userId_safe];
  }
}
// -x-
// downloads the images for +userId+ while checking the cache
// status based on +cache_details+. +type+ specifies which
// image type should be called back on
// callback: error, image hash, slim
function store_images(rid, userId, cache_details, type, callback) {
  if (requests[type]["!" + userId]) {
    logging.debug(rid, "adding to request queue");
    push_request(userId, type, callback);
  } else {
    push_request(userId, type, callback);

    networking.get_profile(rid, userId, function(err, profile) {
      if (err || !profile) {
        // error or uuid without profile
        if (!err && !profile) {
          // no error, but uuid without profile
          cache.save_hash(rid, userId, null, null, undefined, function(cache_err) {
            // we have no profile, so we have neither skin nor cape
            resume(userId, "skin", cache_err, null, false);
            resume(userId, "cape", cache_err, null, false);
          });
        } else {
          // an error occured, not caching. we can try again in 60 seconds
          resume(userId, type, err, null, false);
        }
      } else {
        // no error and we have a profile (if it's a uuid)
        store_skin(rid, userId, profile, cache_details, function(store_err, skin_hash, slim) {
          if (store_err && !skin_hash) {
            // an error occured, not caching. we can try in 60 seconds
            resume(userId, "skin", store_err, null, slim);
          } else {
            cache.save_hash(rid, userId, skin_hash, undefined, slim, function(cache_err) {
              resume(userId, "skin", (store_err || cache_err), skin_hash, slim);
            });
          }
        });
        store_cape(rid, userId, profile, cache_details, function(store_err, cape_hash) {
          if (store_err && !cape_hash) {
            // an error occured, not caching. we can try in 60 seconds
            resume(userId, "cape", (store_err), cape_hash, false);
          } else {
            cache.save_hash(rid, userId, undefined, cape_hash, undefined, function(cache_err) {
              resume(userId, "cape", (store_err || cache_err), cape_hash, false);
            });
          }
        });
      }
    });
  }
}
// -x-
var exp = {};
// -x-
// returns true if the +userId+ is a valid userId
// the UUID might not exist, however
exp.id_valid = function(userId) {
  return valid_user_id.test(userId);
};
// -x-
// decides whether to get a +type+ image for +userId+ from disk or to download it
// callback: error, status, hash, slim
// for status, see response.js
exp.get_image_hash = function(rid, userId, type, callback) {
  cache.get_details(userId, function(err, cache_details) {
    var cached_hash = null;
    if (cache_details !== null) {
      cached_hash = type === "skin" ? cache_details.skin : cache_details.cape;
    }
    if (err) {
      callback(err, -1, null, false);
    } else {
      if (cache_details && cache_details[type] !== undefined && cache_details.time + config.caching.local * 1000 >= Date.now()) {
        // use cached image
        logging.debug(rid, "userId cached & recently updated");
        callback(null, (cached_hash ? 1 : 0), cached_hash, cache_details.slim);
      } else {
        // download image
        if (cache_details && cache_details[type] !== undefined) {
          logging.debug(rid, "userId cached, but too old");
          logging.debug(rid, JSON.stringify(cache_details));
        } else {
          logging.debug(rid, "userId not cached");
        }
        store_images(rid, userId, cache_details, type, function(store_err, new_hash, slim) {
          if (store_err) {
            // an error occured, but we have a cached hash
            // (e.g. Mojang servers not reachable, using outdated hash)

            // bump the TTL after hitting the rate limit
            var ratelimited = store_err.code === "RATELIMIT";
            cache.update_timestamp(rid, userId, !ratelimited, function(err2) {
              callback(err2 || store_err, 4, cache_details && cached_hash, slim);
            });
          } else {
            var status = cache_details && (cached_hash === new_hash) ? 3 : 2;
            logging.debug(rid, "cached hash:", (cache_details && cached_hash));
            logging.debug(rid, "new hash:", new_hash);
            callback(null, status, new_hash, slim);
          }
        });
      }
    }
  });
};
// -x-

// handles requests for +userId+ avatars with +size+
// callback: error, status, image buffer, skin hash
// image is the user's face+overlay when overlay is true, or the face otherwise
// for status, see get_image_hash
exp.get_avatar = function(rid, userId, overlay, size, callback) {
  exp.get_image_hash(rid, userId, "skin", function(err, status, skin_hash, slim) {
    if (skin_hash) {
      var facepath = path.join(config.directories.faces, skin_hash + ".png");
      var helmpath = path.join(config.directories.helms, skin_hash + ".png");
      var filepath = facepath;
      fs.access(helmpath, function(fs_err) {
        if (overlay && !fs_err) {
          filepath = helmpath;
        }
        skins.resize_img(filepath, size, function(img_err, image) {
          if (img_err) {
            callback(img_err, -1, null, skin_hash);
          } else {
            status = err ? -1 : status;
            callback(err, status, image, skin_hash);
          }
        });
      });
    } else {
      // hash is null when userId has no skin
      callback(err, status, null, null);
    }
  });
};
// -x-
// handles requests for +userId+ skins
// callback: error, skin hash, status, image buffer, slim
exp.get_skin = function(rid, userId, callback) {
  exp.get_image_hash(rid, userId, "skin", function(err, status, skin_hash, slim) {
    if (skin_hash) {
      var skinpath = path.join(config.directories.skins, skin_hash + ".png");
      fs.access(skinpath, function(fs_err) {
        if (!fs_err) {
          logging.debug(rid, "skin already exists, not downloading");
          skins.open_skin(rid, skinpath, function(skin_err, img) {
            callback(skin_err || err, skin_hash, status, img, slim);
          });
        } else {
          networking.save_texture(rid, skin_hash, skinpath, function(net_err, response, img) {
            callback(net_err || err, skin_hash, status, img, slim);
          });
        }
      });
    } else {
      callback(err, null, status, null, slim);
    }
  });
};
// -x-
// helper method used for file names
// possible returned names based on +overlay+ and +body+ are:
// body, bodyhelm, head, headhelm
function get_type(overlay, body) {
  var text = body ? "body" : "head";
  return overlay ? text + "helm" : text;
}
// -x-
// handles creations of 3D renders
// callback: error, status, skin hash, image buffer
exp.get_render = function(rid, userId, scale, overlay, body, callback) {
  exp.get_skin(rid, userId, function(err, skin_hash, status, img, slim) {
    if (!skin_hash) {
      callback(err, status, skin_hash, null);
      return;
    }
    var renderpath = path.join(config.directories.renders, [skin_hash, scale, get_type(overlay, body), slim ? "s" : "t"].join("-") + ".png");
    fs.access(renderpath, function(fs_err) {
      if (!fs_err) {
        renders.open_render(rid, renderpath, function(render_err, rendered_img) {
          callback(render_err, 1, skin_hash, rendered_img);
        });
        return;
      } else {
        if (!img) {
          callback(err, 0, skin_hash, null);
          return;
        }
        renders.draw_model(rid, img, scale, overlay, body, slim || userId.toLowerCase() === "mhf_alex", function(draw_err, drawn_img) {
          if (draw_err) {
            callback(draw_err, -1, skin_hash, null);
          } else if (!drawn_img) {
            callback(null, 0, skin_hash, null);
          } else {
            fs.writeFile(renderpath, drawn_img, "binary", function(write_err) {
              callback(write_err, status, skin_hash, drawn_img);
            });
          }
        });
      }
    });
  });
};
// -x-
// handles requests for +userId+ capes
// callback: error, cape hash, status, image buffer
exp.get_cape = function(rid, userId, callback) {
  exp.get_image_hash(rid, userId, "cape", function(err, status, cape_hash, slim) {
    if (!cape_hash) {
      callback(err, null, status, null);
      return;
    }
    var capepath = path.join(config.directories.capes, cape_hash + ".png");
    fs.access(capepath, function(fs_err) {
      if (!fs_err) {
        logging.debug(rid, "cape already exists, not downloading");
        skins.open_skin(rid, capepath, function(skin_err, img) {
          callback(skin_err || err, cape_hash, status, img);
        });
      } else {
        networking.save_texture(rid, cape_hash, capepath, function(net_err, response, img) {
          if (response && response.statusCode === 404) {
            callback(net_err, cape_hash, status, null);
          } else {
            callback(net_err, cape_hash, status, img);
          }
        });
      }
    });
  });
};
// -x-
exp.stoplog = function() {
  clearInterval(loginterval);
}
// -x-
module.exports = exp;
// -x-
var config = require("../config");
// -x-
var exp = {};

// returns all values in the +args+ object separated by " "
function join_args(args) {
  var values = [];
  for (var i = 0, l = args.length; i < l; i++) {
    values.push(args[i]);
  }
  return values.join(" ");
}
// -x-
// prints +args+ to +logger+ (defaults to `console.log`)
// the +level+ and a timestamp is prepended to each line of log
// the timestamp can be disabled in the config
function log(level, args, logger) {
  logger = logger || console.log;
  var time = config.server.log_time ? new Date().toISOString() + " " : "";
  var lines = join_args(args).split("\n");
  for (var i = 0, l = lines.length; i < l; i++) {
    logger(time, level + ":", lines[i]);
  }
}
// -x-
// log with INFO level
exp.log = function() {
  log(" INFO", arguments);
};
// -x-
// log with WARN level
exp.warn = function() {
  log(" WARN", arguments, console.warn);
};
// log with ERROR level
exp.error = function() {
  log("ERROR", arguments, console.error);
};
// -x-
// log with DEBUG level if debug logging is enabled
if (config.server.debug_enabled) {
  exp.debug = function() {
    log("DEBUG", arguments);
  };
} else {
  exp.debug = function() {};
}
// -x-

module.exports = exp;
// -x-