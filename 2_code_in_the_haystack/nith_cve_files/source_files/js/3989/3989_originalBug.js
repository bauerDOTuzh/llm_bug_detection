useServerInsertedHTML(() => {
    // This only happens on the server
    stream.push(...(props.onFlush?.() ?? []))

    if (!stream.length) {
      return null
    }
    // console.log(`pushing ${stream.length} entries`)
      const serializedCacheArgs = stream
        .map((entry) => transformer.serialize(entry))
        .map((entry) => JSON.stringify(entry))
        .join(',')

    // Flush stream
    stream.length = 0

    const html: Array<string> = [
      `window[${idJSON}] = window[${idJSON}] || [];`,
      `window[${idJSON}].push(${serializedCacheArgs});`,
    ]
    return (
      <script
        key={count.current++}
        dangerouslySetInnerHTML={{
          __html: html.join(''),
        }}
      />
    )
  })
  // </server stuff>