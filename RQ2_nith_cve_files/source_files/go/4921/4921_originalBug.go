func OrderAndPaginate(c *gin.Context) func(db *gorm.DB) *gorm.DB {
	return func(db *gorm.DB) *gorm.DB {
		sort := c.DefaultQuery("order", "desc")

		order := fmt.Sprintf("`%s` %s", DefaultQuery(c, "sort_by", "id"), sort)
		db = db.Order(order)

		page := cast.ToInt(c.Query("page"))
		if page == 0 {
			page = 1
		}
		pageSize := settings.ServerSettings.PageSize
		reqPageSize := c.Query("page_size")
		if reqPageSize != "" {
			pageSize = cast.ToInt(reqPageSize)
		}
		offset := (page - 1) * pageSize

		return db.Offset(offset).Limit(pageSize)
	}
}