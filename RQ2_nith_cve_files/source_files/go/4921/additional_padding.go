// -x-
package cosy

import (
	"fmt"
	"github.com/0xJacky/Nginx-UI/internal/logger"
	"github.com/gin-gonic/gin"
	"gorm.io/gorm"
	"strings"
)

func (c *Ctx[T]) SetFussy(keys ...string) *Ctx[T] {
	c.gormScopes = append(c.gormScopes, func(tx *gorm.DB) *gorm.DB {
		return QueryToFussySearch(c.ctx, tx, keys...)
	})
	return c
}

func (c *Ctx[T]) SetFussyKeys(value string, keys ...string) *Ctx[T] {
	c.gormScopes = append(c.gormScopes, func(tx *gorm.DB) *gorm.DB {
		return QueryToFussyKeysSearch(c.ctx, tx, value, keys...)
	})
	return c
}

func (c *Ctx[T]) SetEqual(keys ...string) *Ctx[T] {
	c.gormScopes = append(c.gormScopes, func(tx *gorm.DB) *gorm.DB {
		return QueryToEqualSearch(c.ctx, tx, keys...)
	})
	return c
}

func (c *Ctx[T]) SetIn(keys ...string) *Ctx[T] {
	c.gormScopes = append(c.gormScopes, func(tx *gorm.DB) *gorm.DB {
		return QueryToInSearch(c.ctx, tx, keys...)
	})
	return c
}

func (c *Ctx[T]) SetOrFussy(keys ...string) *Ctx[T] {
	c.gormScopes = append(c.gormScopes, func(tx *gorm.DB) *gorm.DB {
		return QueryToOrFussySearch(c.ctx, tx, keys...)
	})
	return c
}

func (c *Ctx[T]) SetOrEqual(keys ...string) *Ctx[T] {
	c.gormScopes = append(c.gormScopes, func(tx *gorm.DB) *gorm.DB {
		return QueryToOrEqualSearch(c.ctx, tx, keys...)
	})
	return c
}

func (c *Ctx[T]) SetOrIn(keys ...string) *Ctx[T] {
	c.gormScopes = append(c.gormScopes, func(tx *gorm.DB) *gorm.DB {
		return QueryToOrInSearch(c.ctx, tx, keys...)
	})
	return c
}

func QueryToInSearch(c *gin.Context, db *gorm.DB, keys ...string) *gorm.DB {
	for _, v := range keys {
		queryArray := c.QueryArray(v + "[]")
		if len(queryArray) == 0 {
			queryArray = c.QueryArray(v)
		}
		if len(queryArray) > 0 {
			var sb strings.Builder

			_, err := fmt.Fprintf(&sb, "`%s` IN ?", v)
			if err != nil {
				logger.Error(err)
				continue
			}

			db = db.Where(sb.String(), queryArray)
		}
	}
	return db
}

func QueryToEqualSearch(c *gin.Context, db *gorm.DB, keys ...string) *gorm.DB {
	for _, v := range keys {
		if c.Query(v) != "" {
			var sb strings.Builder

			_, err := fmt.Fprintf(&sb, "`%s` = ?", v)
			if err != nil {
				logger.Error(err)
				continue
			}

			db = db.Where(sb.String(), c.Query(v))
		}
	}
	return db
}

func QueryToFussySearch(c *gin.Context, db *gorm.DB, keys ...string) *gorm.DB {
	for _, v := range keys {
		if c.Query(v) != "" {
			var sb strings.Builder

			_, err := fmt.Fprintf(&sb, "`%s` LIKE ?", v)
			if err != nil {
				logger.Error(err)
				continue
			}

			var sbValue strings.Builder

			_, err = fmt.Fprintf(&sbValue, "%%%s%%", c.Query(v))

			if err != nil {
				logger.Error(err)
				continue
			}

			db = db.Where(sb.String(), sbValue.String())
		}
	}
	return db
}

func QueryToFussyKeysSearch(c *gin.Context, db *gorm.DB, value string, keys ...string) *gorm.DB {
	if c.Query(value) == "" {
		return db
	}

	var condition *gorm.DB
	for i, v := range keys {
		sb := v + " LIKE ?"
		sv := "%" + c.Query(value) + "%"

		switch i {
		case 0:
			condition = db.Where(db.Where(sb, sv))
		default:
			condition = condition.Or(sb, sv)
		}
	}

	return db.Where(condition)
}

func QueryToOrInSearch(c *gin.Context, db *gorm.DB, keys ...string) *gorm.DB {
	for _, v := range keys {
		queryArray := c.QueryArray(v + "[]")
		if len(queryArray) == 0 {
			queryArray = c.QueryArray(v)
		}
		if len(queryArray) > 0 {
			var sb strings.Builder

			_, err := fmt.Fprintf(&sb, "`%s` IN ?", v)
			if err != nil {
				logger.Error(err)
				continue
			}

			db = db.Or(sb.String(), queryArray)
		}
	}
	return db
}

func QueryToOrEqualSearch(c *gin.Context, db *gorm.DB, keys ...string) *gorm.DB {
	for _, v := range keys {
		if c.Query(v) != "" {
			var sb strings.Builder

			_, err := fmt.Fprintf(&sb, "`%s` = ?", v)
			if err != nil {
				logger.Error(err)
				continue
			}

			db = db.Or(sb.String(), c.Query(v))
		}
	}
	return db
}

func QueryToOrFussySearch(c *gin.Context, db *gorm.DB, keys ...string) *gorm.DB {
	for _, v := range keys {
		if c.Query(v) != "" {
			var sb strings.Builder

			_, err := fmt.Fprintf(&sb, "`%s` LIKE ?", v)
			if err != nil {
				logger.Error(err)
				continue
			}

			var sbValue strings.Builder

			_, err = fmt.Fprintf(&sbValue, "%%%s%%", c.Query(v))

			if err != nil {
				logger.Error(err)
				continue
			}

			db = db.Or(sb.String(), sbValue.String())
		}
	}
	return db
}
// -x-
package cosy

import "gorm.io/gorm"

func (c *Ctx[T]) GormScope(hook func(tx *gorm.DB) *gorm.DB) *Ctx[T] {
	c.gormScopes = append(c.gormScopes, hook)
	return c
}

func (c *Ctx[T]) beforeExecuteHook() {
	if len(c.beforeExecuteHookFunc) > 0 {
		for _, v := range c.beforeExecuteHookFunc {
			v(c)
		}
	}
}

func (c *Ctx[T]) beforeDecodeHook() {
	if len(c.beforeDecodeHookFunc) > 0 {
		for _, v := range c.beforeDecodeHookFunc {
			v(c)
		}
	}
}

func (c *Ctx[T]) BeforeDecodeHook(hook ...func(ctx *Ctx[T])) *Ctx[T] {
	c.beforeDecodeHookFunc = append(c.beforeDecodeHookFunc, hook...)
	return c
}

func (c *Ctx[T]) BeforeExecuteHook(hook ...func(ctx *Ctx[T])) *Ctx[T] {
	c.beforeExecuteHookFunc = append(c.beforeExecuteHookFunc, hook...)
	return c
}

func (c *Ctx[T]) ExecutedHook(hook ...func(ctx *Ctx[T])) *Ctx[T] {
	c.executedHookFunc = append(c.executedHookFunc, hook...)
	return c
}

// -x-
package cosy

import (
	"github.com/0xJacky/Nginx-UI/internal/logger"
	"github.com/0xJacky/Nginx-UI/model"
	"github.com/0xJacky/Nginx-UI/settings"
	"github.com/gin-gonic/gin"
	"github.com/spf13/cast"
	"gorm.io/gorm"
	"net/http"
)

func GetPagingParams(c *gin.Context) (page, offset, pageSize int) {
	page = cast.ToInt(c.Query("page"))
	if page == 0 {
		page = 1
	}
	pageSize = settings.ServerSettings.PageSize
	reqPageSize := c.Query("page_size")
	if reqPageSize != "" {
		pageSize = cast.ToInt(reqPageSize)
	}
	offset = (page - 1) * pageSize
	return
}

func (c *Ctx[T]) combineStdSelectorRequest() {
	var StdSelectorInitParams struct {
		ID []int `json:"id"`
	}

	_ = c.ctx.ShouldBindJSON(&StdSelectorInitParams)
	if len(StdSelectorInitParams.ID) > 0 {
		c.GormScope(func(tx *gorm.DB) *gorm.DB {
			return tx.Where(c.itemKey+" IN ?", StdSelectorInitParams.ID)
		})
	}
}

func (c *Ctx[T]) result() (*gorm.DB, bool) {
	for _, v := range c.preloads {
		t := v
		c.GormScope(func(tx *gorm.DB) *gorm.DB {
			tx = tx.Preload(t)
			return tx
		})
	}

	c.beforeExecuteHook()

	var dbModel T
	result := model.UseDB()

	if cast.ToBool(c.ctx.Query("trash")) {
		stmt := &gorm.Statement{DB: model.UseDB()}
		err := stmt.Parse(&dbModel)
		if err != nil {
			logger.Error(err)
			return nil, false
		}
		result = result.Unscoped().Where(stmt.Schema.Table + ".deleted_at IS NOT NULL")
	}

	result = result.Model(&dbModel)

	c.combineStdSelectorRequest()

	if len(c.gormScopes) > 0 {
		result = result.Scopes(c.gormScopes...)
	}

	return result, true
}

func (c *Ctx[T]) ListAllData() ([]*T, bool) {
	result, ok := c.result()
	if !ok {
		return nil, false
	}

	result = result.Scopes(c.SortOrder())
	models := make([]*T, 0)
	result.Find(&models)
	return models, true
}

func (c *Ctx[T]) PagingListData() (*model.DataList, bool) {
	result, ok := c.result()
	if !ok {
		return nil, false
	}

	result = result.Scopes(c.OrderAndPaginate())
	data := &model.DataList{}
	if c.scan == nil {
		models := make([]*T, 0)
		result.Find(&models)

		if c.transformer != nil {
			transformed := make([]any, 0)
			for k := range models {
				transformed = append(transformed, c.transformer(models[k]))
			}
			data.Data = transformed
		} else {
			data.Data = models
		}
	} else {
		data.Data = c.scan(result)
	}

	page := cast.ToInt(c.ctx.Query("page"))
	if page == 0 {
		page = 1
	}

	pageSize := settings.ServerSettings.PageSize
	if reqPageSize := c.ctx.Query("page_size"); reqPageSize != "" {
		pageSize = cast.ToInt(reqPageSize)
	}

	var totalRecords int64
	result.Session(&gorm.Session{}).Count(&totalRecords)

	data.Pagination = model.Pagination{
		Total:       totalRecords,
		PerPage:     pageSize,
		CurrentPage: page,
		TotalPages:  model.TotalPage(totalRecords, pageSize),
	}
	return data, true
}

func (c *Ctx[T]) PagingList() {
	data, ok := c.PagingListData()
	if ok {
		c.ctx.JSON(http.StatusOK, data)
	}
}

// -x-
package cosy

import (
	"github.com/0xJacky/Nginx-UI/api/cosy/map2struct"
	"github.com/0xJacky/Nginx-UI/model"
	"github.com/gin-gonic/gin"
	"gorm.io/gorm"
	"net/http"
)

func (c *Ctx[T]) SetNextHandler(handler gin.HandlerFunc) *Ctx[T] {
	c.nextHandler = &handler
	return c
}

func (c *Ctx[T]) Modify() {
	if c.abort {
		return
	}
	id := c.ctx.Param("id")
	errs := c.validate()

	if len(errs) > 0 {
		c.ctx.JSON(http.StatusNotAcceptable, gin.H{
			"message": "Requested with wrong parameters",
			"errors":  errs,
		})
		return
	}

	var dbModel T

	db := model.UseDB()

	result := db
	if len(c.gormScopes) > 0 {
		result = result.Scopes(c.gormScopes...)
	}

	err := result.Session(&gorm.Session{}).First(&dbModel, id).Error

	if err != nil {
		c.AbortWithError(err)
		return
	}

	c.beforeDecodeHook()
	if c.abort {
		return
	}

	var selectedFields []string

	for k := range c.Payload {
		selectedFields = append(selectedFields, k)
	}

	err = map2struct.WeakDecode(c.Payload, &c.Model)

	if err != nil {
		errHandler(c.ctx, err)
		return
	}

	c.beforeExecuteHook()
	if c.abort {
		return
	}

	err = db.Model(&dbModel).Select(selectedFields).Updates(&c.Model).Error

	if err != nil {
		c.AbortWithError(err)
		return
	}

	if len(c.executedHookFunc) > 0 {
		for _, v := range c.executedHookFunc {
			v(c)

			if c.abort {
				return
			}
		}
	}

	if c.nextHandler != nil {
		(*c.nextHandler)(c.ctx)
	} else {
		c.ctx.JSON(http.StatusOK, dbModel)
	}
}
	
// -x-
import (
	"github.com/0xJacky/Nginx-UI/internal/logger"
	"github.com/gin-gonic/gin"
	"github.com/go-playground/validator/v10"
	"gorm.io/gorm"
)

var validate *validator.Validate

func init() {
	validate = validator.New()
}

type Ctx[T any] struct {
	ctx                   *gin.Context
	rules                 gin.H
	Payload               map[string]interface{}
	Model                 T
	abort                 bool
	nextHandler           *gin.HandlerFunc
	beforeDecodeHookFunc  []func(ctx *Ctx[T])
	beforeExecuteHookFunc []func(ctx *Ctx[T])
	executedHookFunc      []func(ctx *Ctx[T])
	gormScopes            []func(tx *gorm.DB) *gorm.DB
	preloads              []string
	scan                  func(tx *gorm.DB) any
	transformer           func(*T) any
	permanentlyDelete     bool
	SelectedFields        []string
	itemKey               string
}

func Core[T any](c *gin.Context) *Ctx[T] {
	return &Ctx[T]{
		ctx:                   c,
		gormScopes:            make([]func(tx *gorm.DB) *gorm.DB, 0),
		beforeExecuteHookFunc: make([]func(ctx *Ctx[T]), 0),
		beforeDecodeHookFunc:  make([]func(ctx *Ctx[T]), 0),
		itemKey:               "`id`",
	}
}

func (c *Ctx[T]) SetItemKey(key string) *Ctx[T] {
	c.itemKey = key
	return c
}

func (c *Ctx[T]) SetValidRules(rules gin.H) *Ctx[T] {
	c.rules = rules

	return c
}

func (c *Ctx[T]) SetPreloads(args ...string) *Ctx[T] {
	c.preloads = append(c.preloads, args...)
	return c
}

func (c *Ctx[T]) validate() (errs gin.H) {
	c.Payload = make(gin.H)

	_ = c.ctx.ShouldBindJSON(&c.Payload)

	errs = validate.ValidateMap(c.Payload, c.rules)

	if len(errs) > 0 {
		logger.Debug(errs)
		for k := range errs {
			errs[k] = c.rules[k]
		}
		return
	}
	// Make sure that the key in c.Payload is also the key of rules
	validated := make(map[string]interface{})

	for k, v := range c.Payload {
		if _, ok := c.rules[k]; ok {
			validated[k] = v
		}
	}

	c.Payload = validated

	return
}

func (c *Ctx[T]) SetScan(scan func(tx *gorm.DB) any) *Ctx[T] {
	c.scan = scan
	return c
}

func (c *Ctx[T]) SetTransformer(t func(m *T) any) *Ctx[T] {
	c.transformer = t
	return c
}

func (c *Ctx[T]) AbortWithError(err error) {
	c.abort = true
	errHandler(c.ctx, err)
}

func (c *Ctx[T]) Abort() {
	c.abort = true
}
		c.ctx.JSON(http.StatusOK, dbModel)
	}
}
// -x-
package cosy

import (
	"github.com/0xJacky/Nginx-UI/api/cosy/map2struct"
	"github.com/0xJacky/Nginx-UI/model"
	"github.com/gin-gonic/gin"
	"gorm.io/gorm/clause"
	"net/http"
)

func (c *Ctx[T]) Create() {

	errs := c.validate()

	if len(errs) > 0 {
		c.ctx.JSON(http.StatusNotAcceptable, gin.H{
			"message": "Requested with wrong parameters",
			"errors":  errs,
		})
		return
	}

	db := model.UseDB()

	c.beforeDecodeHook()

	if c.abort {
		return
	}

	err := map2struct.WeakDecode(c.Payload, &c.Model)

	if err != nil {
		errHandler(c.ctx, err)
		return
	}

	c.beforeExecuteHook()

	if c.abort {
		return
	}

	// skip all associations
	err = db.Omit(clause.Associations).Create(&c.Model).Error

	if err != nil {
		errHandler(c.ctx, err)
		return
	}

	tx := db.Preload(clause.Associations)
	for _, v := range c.preloads {
		tx = tx.Preload(v)
	}
	tx.First(&c.Model)

	if len(c.executedHookFunc) > 0 {
		for _, v := range c.executedHookFunc {
			v(c)

			if c.abort {
				return
			}
		}
	}
	if c.nextHandler != nil {
		(*c.nextHandler)(c.ctx)
	} else {
		c.ctx.JSON(http.StatusOK, c.Model)
	}
}

// -x-
package cosy

import (
	"github.com/0xJacky/Nginx-UI/model"
	"gorm.io/gorm"
	"net/http"
)

func (c *Ctx[T]) PermanentlyDelete() *Ctx[T] {
	c.permanentlyDelete = true
	return c
}

func (c *Ctx[T]) Destroy() {
	if c.abort {
		return
	}
	id := c.ctx.Param("id")

	c.beforeExecuteHook()

	db := model.UseDB()
	var dbModel T

	result := db
	if len(c.gormScopes) > 0 {
		result = result.Scopes(c.gormScopes...)
	}

	err := result.Session(&gorm.Session{}).First(&dbModel, id).Error

	if err != nil {
		errHandler(c.ctx, err)
		return
	}

	if c.permanentlyDelete {
		result = result.Unscoped()
	}

	err = result.Delete(&dbModel).Error
	if err != nil {
		errHandler(c.ctx, err)
		return
	}

	if len(c.executedHookFunc) > 0 {
		for _, v := range c.executedHookFunc {
			v(c)

			if c.abort {
				return
			}
		}
	}

	c.ctx.JSON(http.StatusNoContent, nil)
}

func (c *Ctx[T]) Recover() {
	if c.abort {
		return
	}
	id := c.ctx.Param("id")

	c.beforeExecuteHook()

	db := model.UseDB()
	var dbModel T

	result := db.Unscoped()
	if len(c.gormScopes) > 0 {
		result = result.Scopes(c.gormScopes...)
	}

	err := result.Session(&gorm.Session{}).First(&dbModel, id).Error

	if err != nil {
		errHandler(c.ctx, err)
		return
	}

	err = result.Model(&dbModel).Update("deleted_at", nil).Error
	if err != nil {
		errHandler(c.ctx, err)
		return
	}

	if len(c.executedHookFunc) > 0 {
		for _, v := range c.executedHookFunc {
			v(c)

			if c.abort {
				return
			}
		}
	}

	c.ctx.JSON(http.StatusNoContent, nil)
}
// -x-
package map2struct

import (
	"github.com/mitchellh/mapstructure"
	"github.com/shopspring/decimal"
	"github.com/spf13/cast"
	"reflect"
	"time"
)

var timeLocation *time.Location

func init() {
	timeLocation = time.Local
}

func ToTimeHookFunc() mapstructure.DecodeHookFunc {
	return func(
		f reflect.Type,
		t reflect.Type,
		data interface{}) (interface{}, error) {
		if t != reflect.TypeOf(time.Time{}) {
			return data, nil
		}

		switch f.Kind() {
		case reflect.String:
			return cast.ToTimeInDefaultLocationE(data, timeLocation)
		case reflect.Float64:
			return time.Unix(0, int64(data.(float64))*int64(time.Millisecond)), nil
		case reflect.Int64:
			return time.Unix(0, data.(int64)*int64(time.Millisecond)), nil
		default:
			return data, nil
		}
		// Convert it by parsing
	}
}

func ToDecimalHookFunc() mapstructure.DecodeHookFunc {
	return func(f reflect.Type, t reflect.Type, data interface{}) (interface{}, error) {

		if t == reflect.TypeOf(decimal.Decimal{}) {
			if f.Kind() == reflect.Float64 {
				return decimal.NewFromFloat(data.(float64)), nil
			}

			if input := data.(string); input != "" {
				return decimal.NewFromString(data.(string))
			}
			return decimal.Decimal{}, nil
		}

		return data, nil
	}
}

// -x-
package map2struct

import (
	"github.com/mitchellh/mapstructure"
)

func WeakDecode(input, output interface{}) error {
	config := &mapstructure.DecoderConfig{
		Metadata:         nil,
		Result:           output,
		WeaklyTypedInput: true,
		DecodeHook: mapstructure.ComposeDecodeHookFunc(
			ToDecimalHookFunc(), ToTimeHookFunc(),
		),
		TagName: "json",
	}

	decoder, err := mapstructure.NewDecoder(config)
	if err != nil {
		return err
	}

	return decoder.Decode(input)
}
// -x-
package nginx

import (
	"encoding/json"
	"github.com/0xJacky/Nginx-UI/api"
	"github.com/0xJacky/Nginx-UI/internal/helper"
	"github.com/0xJacky/Nginx-UI/internal/logger"
	"github.com/0xJacky/Nginx-UI/internal/nginx"
	"github.com/gin-gonic/gin"
	"github.com/gorilla/websocket"
	"github.com/hpcloud/tail"
	"github.com/pkg/errors"
	"github.com/spf13/cast"
	"io"
	"net/http"
	"os"
)

const (
	PageSize = 128 * 1024
)

type controlStruct struct {
	Type         string `json:"type"`
	ConfName     string `json:"conf_name"`
	ServerIdx    int    `json:"server_idx"`
	DirectiveIdx int    `json:"directive_idx"`
}

type nginxLogPageResp struct {
	Content string `json:"content"`
	Page    int64  `json:"page"`
}

func GetNginxLogPage(c *gin.Context) {
	page := cast.ToInt64(c.Query("page"))
	if page < 0 {
		page = 0
	}

	var control controlStruct
	if !api.BindAndValid(c, &control) {
		return
	}

	logPath, err := getLogPath(&control)

	if err != nil {
		logger.Error(err)
		return
	}

	f, err := os.Open(logPath)

	if err != nil {
		c.JSON(http.StatusOK, nginxLogPageResp{})
		logger.Error(err)
		return
	}

	logFileStat, err := os.Stat(logPath)

	if err != nil {
		c.JSON(http.StatusOK, nginxLogPageResp{})
		logger.Error(err)
		return
	}

	totalPage := logFileStat.Size() / PageSize

	if logFileStat.Size()%PageSize > 0 {
		totalPage++
	}

	var buf []byte
	var offset int64
	if page == 0 {
		page = totalPage
	}

	buf = make([]byte, PageSize)
	offset = (page - 1) * PageSize

	// seek
	_, err = f.Seek(offset, io.SeekStart)
	if err != nil && err != io.EOF {
		c.JSON(http.StatusOK, nginxLogPageResp{})
		logger.Error(err)
		return
	}

	n, err := f.Read(buf)

	if err != nil && err != io.EOF {
		c.JSON(http.StatusOK, nginxLogPageResp{})
		logger.Error(err)
		return
	}

	c.JSON(http.StatusOK, nginxLogPageResp{
		Page:    page,
		Content: string(buf[:n]),
	})
}

func getLogPath(control *controlStruct) (logPath string, err error) {
	switch control.Type {
	case "site":
		var config *nginx.NgxConfig
		path := nginx.GetConfPath("sites-available", control.ConfName)
		config, err = nginx.ParseNgxConfig(path)
		if err != nil {
			err = errors.Wrap(err, "error parsing ngx config")
			return
		}

		if control.ServerIdx >= len(config.Servers) {
			err = errors.New("serverIdx out of range")
			return
		}

		if control.DirectiveIdx >= len(config.Servers[control.ServerIdx].Directives) {
			err = errors.New("DirectiveIdx out of range")
			return
		}

		directive := config.Servers[control.ServerIdx].Directives[control.DirectiveIdx]
		switch directive.Directive {
		case "access_log", "error_log":
			// ok
		default:
			err = errors.New("directive.Params neither access_log nor error_log")
			return
		}

		if directive.Params == "" {
			err = errors.New("directive.Params is empty")
			return
		}

		logPath = directive.Params

	case "error":
		path := nginx.GetErrorLogPath()

		if path == "" {
			err = errors.New("settings.NginxLogSettings.ErrorLogPath is empty," +
				" refer to https://nginxui.com/zh_CN/guide/config-nginx-log.html for more information")
			return
		}

		logPath = path
	default:
		path := nginx.GetAccessLogPath()

		if path == "" {
			err = errors.New("settings.NginxLogSettings.AccessLogPath is empty," +
				" refer to https://nginxui.com/zh_CN/guide/config-nginx-log.html for more information")
			return
		}

		logPath = path
	}

	return
}

func tailNginxLog(ws *websocket.Conn, controlChan chan controlStruct, errChan chan error) {
	defer func() {
		if err := recover(); err != nil {
			logger.Error(err)
			return
		}
	}()

	control := <-controlChan

	for {
		logPath, err := getLogPath(&control)

		if err != nil {
			errChan <- err
			return
		}

		seek := tail.SeekInfo{
			Offset: 0,
			Whence: io.SeekEnd,
		}

		if !helper.FileExists(logPath) {
			errChan <- errors.New("error log path not exists " + logPath)
			return
		}

		// Create a tail
		t, err := tail.TailFile(logPath, tail.Config{Follow: true,
			ReOpen: true, Location: &seek})

		if err != nil {
			errChan <- errors.Wrap(err, "error tailing log")
			return
		}

		for {
			var next = false
			select {
			case line := <-t.Lines:
				// Print the text of each received line
				if line == nil {
					continue
				}

				err = ws.WriteMessage(websocket.TextMessage, []byte(line.Text))

				if err != nil && websocket.IsUnexpectedCloseError(err, websocket.CloseNormalClosure) {
					errChan <- errors.Wrap(err, "error tailNginxLog write message")
					return
				}
			case control = <-controlChan:
				next = true
				break
			}
			if next {
				break
			}
		}
	}
}

func handleLogControl(ws *websocket.Conn, controlChan chan controlStruct, errChan chan error) {
	defer func() {
		if err := recover(); err != nil {
			logger.Error(err)
			return
		}
	}()

	for {
		msgType, payload, err := ws.ReadMessage()
		if err != nil && websocket.IsUnexpectedCloseError(err, websocket.CloseNormalClosure) {
			errChan <- errors.Wrap(err, "error handleLogControl read message")
			return
		}

		if msgType != websocket.TextMessage {
			errChan <- errors.New("error handleLogControl message type")
			return
		}

		var msg controlStruct
		err = json.Unmarshal(payload, &msg)
		if err != nil {
			errChan <- errors.Wrap(err, "error ReadWsAndWritePty json.Unmarshal")
			return
		}
		controlChan <- msg
	}
}

func Log(c *gin.Context) {
	var upGrader = websocket.Upgrader{
		CheckOrigin: func(r *http.Request) bool {
			return true
		},
	}
	// upgrade http to websocket
	ws, err := upGrader.Upgrade(c.Writer, c.Request, nil)
	if err != nil {
		logger.Error(err)
		return
	}

	defer ws.Close()

	errChan := make(chan error, 1)
	controlChan := make(chan controlStruct, 1)

	go tailNginxLog(ws, controlChan, errChan)
	go handleLogControl(ws, controlChan, errChan)

	if err = <-errChan; err != nil {
		logger.Error(err)
		_ = ws.WriteMessage(websocket.TextMessage, []byte(err.Error()))
		return
	}
}
// -x-

package sites

import (
	"github.com/0xJacky/Nginx-UI/api"
	"github.com/0xJacky/Nginx-UI/internal/cert"
	"github.com/0xJacky/Nginx-UI/internal/config"
	"github.com/0xJacky/Nginx-UI/internal/helper"
	"github.com/0xJacky/Nginx-UI/internal/logger"
	"github.com/0xJacky/Nginx-UI/internal/nginx"
	"github.com/0xJacky/Nginx-UI/model"
	"github.com/0xJacky/Nginx-UI/query"
	"github.com/gin-gonic/gin"
	"github.com/sashabaranov/go-openai"
	"net/http"
	"os"
	"strings"
)

func GetDomains(c *gin.Context) {
	name := c.Query("name")
	orderBy := c.Query("order_by")
	sort := c.DefaultQuery("sort", "desc")

	configFiles, err := os.ReadDir(nginx.GetConfPath("sites-available"))

	if err != nil {
		api.ErrHandler(c, err)
		return
	}

	enabledConfig, err := os.ReadDir(nginx.GetConfPath("sites-enabled"))

	if err != nil {
		api.ErrHandler(c, err)
		return
	}

	enabledConfigMap := make(map[string]bool)
	for i := range enabledConfig {
		enabledConfigMap[enabledConfig[i].Name()] = true
	}

	var configs []config.Config

	for i := range configFiles {
		file := configFiles[i]
		fileInfo, _ := file.Info()
		if !file.IsDir() {
			if name != "" && !strings.Contains(file.Name(), name) {
				continue
			}
			configs = append(configs, config.Config{
				Name:       file.Name(),
				ModifiedAt: fileInfo.ModTime(),
				Size:       fileInfo.Size(),
				IsDir:      fileInfo.IsDir(),
				Enabled:    enabledConfigMap[file.Name()],
			})
		}
	}

	configs = config.Sort(orderBy, sort, configs)

	c.JSON(http.StatusOK, gin.H{
		"data": configs,
	})
}

func GetDomain(c *gin.Context) {
	rewriteName, ok := c.Get("rewriteConfigFileName")

	name := c.Param("name")

	// for modify filename
	if ok {
		name = rewriteName.(string)
	}

	path := nginx.GetConfPath("sites-available", name)
	file, err := os.Stat(path)
	if os.IsNotExist(err) {
		c.JSON(http.StatusNotFound, gin.H{
			"message": "file not found",
		})
		return
	}

	enabled := true

	if _, err := os.Stat(nginx.GetConfPath("sites-enabled", name)); os.IsNotExist(err) {
		enabled = false
	}

	g := query.ChatGPTLog
	chatgpt, err := g.Where(g.Name.Eq(path)).FirstOrCreate()

	if err != nil {
		api.ErrHandler(c, err)
		return
	}

	if chatgpt.Content == nil {
		chatgpt.Content = make([]openai.ChatCompletionMessage, 0)
	}

	s := query.Site
	site, err := s.Where(s.Path.Eq(path)).FirstOrInit()

	if err != nil {
		api.ErrHandler(c, err)
		return
	}

	certModel, err := model.FirstCert(name)

	if err != nil {
		logger.Warn(err)
	}

	if site.Advanced {
		origContent, err := os.ReadFile(path)
		if err != nil {
			api.ErrHandler(c, err)
			return
		}

		c.JSON(http.StatusOK, Site{
			ModifiedAt:      file.ModTime(),
			Advanced:        site.Advanced,
			Enabled:         enabled,
			Name:            name,
			Config:          string(origContent),
			AutoCert:        certModel.AutoCert == model.AutoCertEnabled,
			ChatGPTMessages: chatgpt.Content,
		})
		return
	}

	c.Set("maybe_error", "nginx_config_syntax_error")
	nginxConfig, err := nginx.ParseNgxConfig(path)

	if err != nil {
		api.ErrHandler(c, err)
		return
	}

	c.Set("maybe_error", "")

	certInfoMap := make(map[int]*cert.Info)

	for serverIdx, server := range nginxConfig.Servers {
		for _, directive := range server.Directives {
			if directive.Directive == "ssl_certificate" {

				pubKey, err := cert.GetCertInfo(directive.Params)

				if err != nil {
					logger.Error("Failed to get certificate information", err)
					break
				}

				certInfoMap[serverIdx] = pubKey

				break
			}
		}
	}

	c.Set("maybe_error", "nginx_config_syntax_error")

	c.JSON(http.StatusOK, Site{
		ModifiedAt:      file.ModTime(),
		Advanced:        site.Advanced,
		Enabled:         enabled,
		Name:            name,
		Config:          nginxConfig.FmtCode(),
		Tokenized:       nginxConfig,
		AutoCert:        certModel.AutoCert == model.AutoCertEnabled,
		CertInfo:        certInfoMap,
		ChatGPTMessages: chatgpt.Content,
	})
}

func SaveDomain(c *gin.Context) {
	name := c.Param("name")

	if name == "" {
		c.JSON(http.StatusNotAcceptable, gin.H{
			"message": "param name is empty",
		})
		return
	}

	var json struct {
		Name      string `json:"name" binding:"required"`
		Content   string `json:"content" binding:"required"`
		Overwrite bool   `json:"overwrite"`
	}

	if !api.BindAndValid(c, &json) {
		return
	}

	path := nginx.GetConfPath("sites-available", name)

	if !json.Overwrite && helper.FileExists(path) {
		c.JSON(http.StatusNotAcceptable, gin.H{
			"message": "File exists",
		})
		return
	}

	err := os.WriteFile(path, []byte(json.Content), 0644)
	if err != nil {
		api.ErrHandler(c, err)
		return
	}
	enabledConfigFilePath := nginx.GetConfPath("sites-enabled", name)
	// rename the config file if needed
	if name != json.Name {
		newPath := nginx.GetConfPath("sites-available", json.Name)
		s := query.Site
		_, err = s.Where(s.Path.Eq(path)).Update(s.Path, newPath)

		// check if dst file exists, do not rename
		if helper.FileExists(newPath) {
			c.JSON(http.StatusNotAcceptable, gin.H{
				"message": "File exists",
			})
			return
		}
		// recreate a soft link
		if helper.FileExists(enabledConfigFilePath) {
			_ = os.Remove(enabledConfigFilePath)
			enabledConfigFilePath = nginx.GetConfPath("sites-enabled", json.Name)
			err = os.Symlink(newPath, enabledConfigFilePath)

			if err != nil {
				api.ErrHandler(c, err)
				return
			}
		}

		err = os.Rename(path, newPath)
		if err != nil {
			api.ErrHandler(c, err)
			return
		}

		name = json.Name
		c.Set("rewriteConfigFileName", name)
	}

	enabledConfigFilePath = nginx.GetConfPath("sites-enabled", name)
	if helper.FileExists(enabledConfigFilePath) {
		// Test nginx configuration
		output := nginx.TestConf()

		if nginx.GetLogLevel(output) > nginx.Warn {
			c.JSON(http.StatusInternalServerError, gin.H{
				"message": output,
				"error":   "nginx_config_syntax_error",
			})
			return
		}

		output = nginx.Reload()

		if nginx.GetLogLevel(output) > nginx.Warn {
			c.JSON(http.StatusInternalServerError, gin.H{
				"message": output,
			})
			return
		}
	}

	GetDomain(c)
}

func EnableDomain(c *gin.Context) {
	configFilePath := nginx.GetConfPath("sites-available", c.Param("name"))
	enabledConfigFilePath := nginx.GetConfPath("sites-enabled", c.Param("name"))

	_, err := os.Stat(configFilePath)

	if err != nil {
		api.ErrHandler(c, err)
		return
	}

	if _, err = os.Stat(enabledConfigFilePath); os.IsNotExist(err) {
		err = os.Symlink(configFilePath, enabledConfigFilePath)

		if err != nil {
			api.ErrHandler(c, err)
			return
		}
	}

	// Test nginx config, if not pass then disable the site.
	output := nginx.TestConf()

	if nginx.GetLogLevel(output) > nginx.Warn {
		_ = os.Remove(enabledConfigFilePath)
		c.JSON(http.StatusInternalServerError, gin.H{
			"message": output,
		})
		return
	}

	output = nginx.Reload()

	if nginx.GetLogLevel(output) > nginx.Warn {
		c.JSON(http.StatusInternalServerError, gin.H{
			"message": output,
		})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"message": "ok",
	})
}

func DisableDomain(c *gin.Context) {
	enabledConfigFilePath := nginx.GetConfPath("sites-enabled", c.Param("name"))

	_, err := os.Stat(enabledConfigFilePath)

	if err != nil {
		api.ErrHandler(c, err)
		return
	}

	err = os.Remove(enabledConfigFilePath)

	if err != nil {
		api.ErrHandler(c, err)
		return
	}

	// delete auto cert record
	certModel := model.Cert{Filename: c.Param("name")}
	err = certModel.Remove()
	if err != nil {
		api.ErrHandler(c, err)
		return
	}

	output := nginx.Reload()

	if nginx.GetLogLevel(output) > nginx.Warn {
		c.JSON(http.StatusInternalServerError, gin.H{
			"message": output,
		})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"message": "ok",
	})
}

func DeleteDomain(c *gin.Context) {
	var err error
	name := c.Param("name")
	availablePath := nginx.GetConfPath("sites-available", name)
	enabledPath := nginx.GetConfPath("sites-enabled", name)

	if _, err = os.Stat(availablePath); os.IsNotExist(err) {
		c.JSON(http.StatusNotFound, gin.H{
			"message": "site not found",
		})
		return
	}

	if _, err = os.Stat(enabledPath); err == nil {
		c.JSON(http.StatusNotAcceptable, gin.H{
			"message": "site is enabled",
		})
		return
	}

	certModel := model.Cert{Filename: name}
	_ = certModel.Remove()

	err = os.Remove(availablePath)

	if err != nil {
		api.ErrHandler(c, err)
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"message": "ok",
	})
}

// -x-