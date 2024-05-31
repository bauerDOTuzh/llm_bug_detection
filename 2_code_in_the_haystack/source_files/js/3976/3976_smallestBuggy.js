{prepend_content}
export async function getHeadingId(
  parser: IMarkdownParser,
  raw: string,
  level: number
) {
  const innerHTML = await parser.render(raw);

  if (!innerHTML) {
    return null;
  }

  const container = document.createElement('div');
  container.innerHTML = innerHTML;
  const header = container.querySelector(`h${level}`);
  if (!header) {
    return null;
  }

  return renderMarkdown.createHeaderId(header);
}
{append_content}