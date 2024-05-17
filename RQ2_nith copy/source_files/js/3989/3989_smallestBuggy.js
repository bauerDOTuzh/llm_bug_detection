{prepend_content}
useServerInsertedHTML(() => {
// This only happens on the server
stream.push(...(props.onFlush?.() ?? []))

const serializedCacheArgs = stream
    .map((entry) => transformer.serialize(entry))
    .map((entry) => JSON.stringify(entry))
    .join(',')

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

{append_content}