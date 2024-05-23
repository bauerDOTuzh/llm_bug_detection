'use client'
// -x-
const serializedSymbol = Symbol('serialized')
// -x-
interface DataTransformer {
  serialize(object: any): any
  deserialize(object: any): any
}
// -x-
type Serialized<TData> = unknown & {
  [serializedSymbol]: TData
}
// -x-
interface TypedDataTransformer<TData> {
  serialize: (obj: TData) => Serialized<TData>
  deserialize: (obj: Serialized<TData>) => TData
}
// -x-
interface HydrationStreamContext<TShape> {
  id: string
  stream: {
    /**
     * **Server method**
     * Push a new entry to the stream
     * Will be ignored on the client
     */
    push: (...shape: Array<TShape>) => void
  }
}
// -x-
export interface HydrationStreamProviderProps<TShape> {
  children: React.ReactNode
  /**
   * Optional transformer to serialize/deserialize the data
   * Example devalue, superjson et al
   */
  transformer?: DataTransformer
  /**
   * **Client method**
   * Called in the browser when new entries are received
   */
  onEntries: (entries: Array<TShape>) => void
  /**
   * **Server method**
   * onFlush is called on the server when the cache is flushed
   */
  onFlush?: () => Array<TShape>
}
// -x-
export function createHydrationStreamProvider<TShape>() {
  const context = React.createContext<HydrationStreamContext<TShape>>(
    null as any,
  )
  /**

   * 1. (Happens on server): `useServerInsertedHTML()` is called **on the server** whenever a `Suspense`-boundary completes
   *    - This means that we might have some new entries in the cache that needs to be flushed
   *    - We pass these to the client by inserting a `<script>`-tag where we do `window[id].push(serializedVersionOfCache)`
   * 2. (Happens in browser) In `useEffect()`:
   *   - We check if `window[id]` is set to an array and call `push()` on all the entries which will call `onEntries()` with the new entries
   *   - We replace `window[id]` with a `push()`-method that will be called whenever new entries are received
   **/
  function UseClientHydrationStreamProvider(props: {
    children: React.ReactNode
    /**
     * Optional transformer to serialize/deserialize the data
     * Example devalue, superjson et al
     */
    transformer?: DataTransformer
    /**
     * **Client method**
     * Called in the browser when new entries are received
     */
    onEntries: (entries: Array<TShape>) => void
    /**
     * **Server method**
     * onFlush is called on the server when the cache is flushed
     */
    onFlush?: () => Array<TShape>
  }) {
    // unique id for the cache provider
    const id = `__RQ${React.useId()}`
    const idJSON = htmlEscapeJsonString(JSON.stringify(id))
// -x-
    const [transformer] = React.useState(
      () =>
        (props.transformer ?? {
          // noop
          serialize: (obj: any) => obj,
          deserialize: (obj: any) => obj,
        }) as unknown as TypedDataTransformer<TShape>,
    )
// -x-
    // <server stuff>
    const [stream] = React.useState<Array<TShape>>(() => {
      if (typeof window !== 'undefined') {
        return {
          push() {
            // no-op on the client
          },
        } as unknown as Array<TShape>
      }
      return []
    })
    const count = React.useRef(0)
// -x- 

    // <client stuff>
    const onEntriesRef = React.useRef(props.onEntries)
    React.useEffect(() => {
      onEntriesRef.current = props.onEntries
    })

    React.useEffect(() => {
      // Client: consume cache:
      const onEntries = (...serializedEntries: Array<Serialized<TShape>>) => {
        const entries = serializedEntries.map((serialized) =>
          transformer.deserialize(serialized),
        )
        onEntriesRef.current(entries)
      }

      const win = window as any
      // Register cache consumer
      const winStream: Array<Serialized<TShape>> = win[id] ?? []

      onEntries(...winStream)

      // Register our own consumer
      win[id] = {
        push: onEntries,
      }

      return () => {
        // Cleanup after unmount
        win[id] = []
      }
    }, [id, transformer])
    // </client stuff>
// -x-
    return (
      <context.Provider value={{ stream, id }}>
        {props.children}
      </context.Provider>
    )
  }
// -x-
  return {
    Provider: UseClientHydrationStreamProvider,
    context,
  }
}

// -x-
function useServerInsertedHTML(props, stream, transformer, idJSON, count) {
  // This only happens on the server
  stream.push(...(props.onFlush?.() ?? []));

  if (!stream.length) {
    return null;
  }

  // Call the function to serialize and generate HTML
  return serializeAndGenerateHTML(stream, transformer, idJSON, count);
}
// -x-