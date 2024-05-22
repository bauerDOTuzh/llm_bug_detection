
/**
 * Find heading with given ID in any of the cells.
 */
async _findHeading(queryId: string): Promise<Private.IScrollTarget | null> {
  // Loop on cells, get headings and search for first matching id.
  for (let cellIdx = 0; cellIdx < this.widgets.length; cellIdx++) {
    const cell = this.widgets[cellIdx];
    if (
      cell.model.type === 'raw' ||
      (cell.model.type === 'markdown' && !(cell as MarkdownCell).rendered)
    ) {
      // Bail early
      continue;
    }
    for (const heading of cell.headings) {
      let id: string | undefined | null = '';
      switch (heading.type) {
        case Cell.HeadingType.HTML:
          id = (heading as TableOfContentsUtils.IHTMLHeading).id;
          break;
        case Cell.HeadingType.Markdown:
          {
            const mdHeading =
              heading as any as TableOfContentsUtils.Markdown.IMarkdownHeading;
            id = await TableOfContentsUtils.Markdown.getHeadingId(
              this.rendermime.markdownParser!,
              mdHeading.raw,
              mdHeading.level
            );
          }
          break;
      }
      if (id === queryId) {
        const element = this.node.querySelector(
          `h${heading.level}[id="${id}"]`
        ) as HTMLElement;

        return {
          cell,
          element
        };
      }
    }
  }
  return null;
}