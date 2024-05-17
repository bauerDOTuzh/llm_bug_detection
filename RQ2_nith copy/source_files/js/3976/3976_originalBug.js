/**
 * Build the heading html id.
 *
 * @param raw Raw markdown heading
 * @param level Heading level
 */
export async function getHeadingId(
  parser: IMarkdownParser,
  raw: string,
  level: number
): Promise<string | null> {
  try {
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
  } catch (reason) {
    console.error('Failed to parse a heading.', reason);
  }

  return null;
}