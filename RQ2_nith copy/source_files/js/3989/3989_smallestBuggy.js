{prepend_content}
function serializeAndGenerateHTML(stream, transformer, idJSON, count) {
    const serializedCacheArgs = stream
      .map((entry) => transformer.serialize(entry))
      .map((entry) => JSON.stringify(entry))
      .join(',');
  
    const html = [
      `window[${idJSON}] = window[${idJSON}] || [];`,
      `window[${idJSON}].push(${serializedCacheArgs});`,
    ];
  
    return (
      <script
        key={count.current++}
        dangerouslySetInnerHTML={{
          __html: html.join(''),
        }}
      />
    );
  }

{append_content}