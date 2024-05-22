{prepend_content}
func applySorting(c *gin.Context, db *gorm.DB) *gorm.DB {
	sort := c.DefaultQuery("order", "desc")
	order := fmt.Sprintf("`%s` %s", DefaultQuery(c, "sort_by", "id"), sort)
	return db.Order(order)
}
{append_content}