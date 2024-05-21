{prepend_content}
def register_changelog_route(app)
  app.get "/changelogs" do
    @filter = params[:filter] || "*"
    @filter = "*" if @filter == ""
    @count = (params[:count] || 100).to_i
    @current_cursor = params[:cursor].to_i
    @prev_cursor = params[:prev_cursor].to_i
    @total_size, @next_cursor, @changelogs = changelog.page(
      cursor: @current_cursor,
      pattern: @filter,
      page_size: @count,
    )

    erb(unique_template(:changelogs))
  end
end
{append_content}