// -x-
type Listener = (focused: boolean) => void

type SetupFn = (
  setFocused: (focused?: boolean) => void,
) => (() => void) | undefined

export class FocusManager extends Subscribable<Listener> {
  #focused?: boolean
  #cleanup?: () => void

  #setup: SetupFn

  constructor() {
    super()
    this.#setup = (onFocus) => {
      // addEventListener does not exist in React Native, but window does
      // eslint-disable-next-line @typescript-eslint/no-unnecessary-condition
      if (!isServer && window.addEventListener) {
        const listener = () => onFocus()
        // Listen to visibilitychange
        window.addEventListener('visibilitychange', listener, false)

        return () => {
          // Be sure to unsubscribe if a new handler is set
          window.removeEventListener('visibilitychange', listener)
        }
      }
      return
    }
  }

  protected onSubscribe(): void {
    if (!this.#cleanup) {
      this.setEventListener(this.#setup)
    }
  }

  protected onUnsubscribe() {
    if (!this.hasListeners()) {
      this.#cleanup?.()
      this.#cleanup = undefined
    }
  }

  setEventListener(setup: SetupFn): void {
    this.#setup = setup
    this.#cleanup?.()
    this.#cleanup = setup((focused) => {
      if (typeof focused === 'boolean') {
        this.setFocused(focused)
      } else {
        this.onFocus()
      }
    })
  }

  setFocused(focused?: boolean): void {
    const changed = this.#focused !== focused
    if (changed) {
      this.#focused = focused
      this.onFocus()
    }
  }

  onFocus(): void {
    const isFocused = this.isFocused()
    this.listeners.forEach((listener) => {
      listener(isFocused)
    })
  }

  isFocused(): boolean {
    if (typeof this.#focused === 'boolean') {
      return this.#focused
    }

    // document global can be unavailable in react native
    // eslint-disable-next-line @typescript-eslint/no-unnecessary-condition
    return globalThis.document?.visibilityState !== 'hidden'
  }
}

export const focusManager = new FocusManager()
// -x-
import type {
    DefaultError,
    MutationKey,
    MutationMeta,
    MutationOptions,
    MutationScope,
    QueryKey,
    QueryMeta,
    QueryOptions,
  } from './types'
  import type { QueryClient } from './queryClient'
  import type { Query, QueryState } from './query'
  import type { Mutation, MutationState } from './mutation'
  
  // TYPES
// -x-
  export interface DehydrateOptions {
    shouldDehydrateMutation?: (mutation: Mutation) => boolean
    shouldDehydrateQuery?: (query: Query) => boolean
  }
// -x-
  export interface HydrateOptions {
    defaultOptions?: {
      queries?: QueryOptions
      mutations?: MutationOptions<unknown, DefaultError, unknown, unknown>
    }
  }
// -x-
  interface DehydratedMutation {
    mutationKey?: MutationKey
    state: MutationState
    meta?: MutationMeta
    scope?: MutationScope
  }
// -x-
  interface DehydratedQuery {
    queryHash: string
    queryKey: QueryKey
    state: QueryState
    meta?: QueryMeta
  }
// -x-
  export interface DehydratedState {
    mutations: Array<DehydratedMutation>
    queries: Array<DehydratedQuery>
  }
// -x-
  // FUNCTIONS
// -x-
  function dehydrateMutation(mutation: Mutation): DehydratedMutation {
    return {
      mutationKey: mutation.options.mutationKey,
      state: mutation.state,
      ...(mutation.options.scope && { scope: mutation.options.scope }),
      ...(mutation.meta && { meta: mutation.meta }),
    }
  }
// -x-  
  // Most config is not dehydrated but instead meant to configure again when
  // consuming the de/rehydrated data, typically with useQuery on the client.
  // Sometimes it might make sense to prefetch data on the server and include
  // in the html-payload, but not consume it on the initial render.
  function dehydrateQuery(query: Query): DehydratedQuery {
    return {
      state: query.state,
      queryKey: query.queryKey,
      queryHash: query.queryHash,
      ...(query.meta && { meta: query.meta }),
    }
  }
// -x-  
  export function defaultShouldDehydrateMutation(mutation: Mutation) {
    return mutation.state.isPaused
  }
// -x- 
  export function defaultShouldDehydrateQuery(query: Query) {
    return query.state.status === 'success'
  }
// -x-  
  export function dehydrate(
    client: QueryClient,
    options: DehydrateOptions = {},
  ): DehydratedState {
    const filterMutation =
      options.shouldDehydrateMutation ?? defaultShouldDehydrateMutation
  
    const mutations = client
      .getMutationCache()
      .getAll()
      .flatMap((mutation) =>
        filterMutation(mutation) ? [dehydrateMutation(mutation)] : [],
      )
  
    const filterQuery =
      options.shouldDehydrateQuery ?? defaultShouldDehydrateQuery
  
    const queries = client
      .getQueryCache()
      .getAll()
      .flatMap((query) => (filterQuery(query) ? [dehydrateQuery(query)] : []))
  
    return { mutations, queries }
  }
// -x-  
  export function hydrate(
    client: QueryClient,
    dehydratedState: unknown,
    options?: HydrateOptions,
  ): void {
    if (typeof dehydratedState !== 'object' || dehydratedState === null) {
      return
    }
    const mutationCache = client.getMutationCache()
    const queryCache = client.getQueryCache()
  
    // eslint-disable-next-line @typescript-eslint/no-unnecessary-condition
    const mutations = (dehydratedState as DehydratedState).mutations || []
    // eslint-disable-next-line @typescript-eslint/no-unnecessary-condition
    const queries = (dehydratedState as DehydratedState).queries || []
  
    mutations.forEach(({ state, ...mutationOptions }) => {
      mutationCache.build(
        client,
        {
          ...options?.defaultOptions?.mutations,
          ...mutationOptions,
        },
        state,
      )
    })
  
    queries.forEach(({ queryKey, state, queryHash, meta }) => {
      const query = queryCache.get(queryHash)
  
      // Do not hydrate if an existing query exists with newer data
      if (query) {
        if (query.state.dataUpdatedAt < state.dataUpdatedAt) {
          // omit fetchStatus from dehydrated state
          // so that query stays in its current fetchStatus
          const { fetchStatus: _ignored, ...dehydratedQueryState } = state
          query.setState(dehydratedQueryState)
        }
        return
      }
  
      // Restore query
      queryCache.build(
        client,
        {
          ...options?.defaultOptions?.queries,
          queryKey,
          queryHash,
          meta,
        },
        // Reset fetch status to idle to avoid
        // query being stuck in fetching state upon hydration
        {
          ...state,
          fetchStatus: 'idle',
        },
      )
    })
  }
// -x-
import { notifyManager } from './notifyManager'
import { Removable } from './removable'
import { createRetryer } from './retryer'
import type {
  DefaultError,
  MutationMeta,
  MutationOptions,
  MutationStatus,
} from './types'
import type { MutationCache } from './mutationCache'
import type { MutationObserver } from './mutationObserver'
import type { Retryer } from './retryer'
// -x-
// TYPES

interface MutationConfig<TData, TError, TVariables, TContext> {
  mutationId: number
  mutationCache: MutationCache
  options: MutationOptions<TData, TError, TVariables, TContext>
  state?: MutationState<TData, TError, TVariables, TContext>
}
// -x-
export interface MutationState<
  TData = unknown,
  TError = DefaultError,
  TVariables = unknown,
  TContext = unknown,
> {
  context: TContext | undefined
  data: TData | undefined
  error: TError | null
  failureCount: number
  failureReason: TError | null
  isPaused: boolean
  status: MutationStatus
  variables: TVariables | undefined
  submittedAt: number
}
// -x-
interface FailedAction<TError> {
  type: 'failed'
  failureCount: number
  error: TError | null
}
// -x-
interface PendingAction<TVariables, TContext> {
  type: 'pending'
  isPaused: boolean
  variables?: TVariables
  context?: TContext
}
// -x-
interface SuccessAction<TData> {
  type: 'success'
  data: TData
}
// -x-
interface ErrorAction<TError> {
  type: 'error'
  error: TError
}

interface PauseAction {
  type: 'pause'
}

interface ContinueAction {
  type: 'continue'
}
// -x-
export type Action<TData, TError, TVariables, TContext> =
  | ContinueAction
  | ErrorAction<TError>
  | FailedAction<TError>
  | PendingAction<TVariables, TContext>
  | PauseAction
  | SuccessAction<TData>

// CLASS
// -x-
export class Mutation<
  TData = unknown,
  TError = DefaultError,
  TVariables = unknown,
  TContext = unknown,
> extends Removable {
  state: MutationState<TData, TError, TVariables, TContext>
  options!: MutationOptions<TData, TError, TVariables, TContext>
  readonly mutationId: number

  #observers: Array<MutationObserver<TData, TError, TVariables, TContext>>
  #mutationCache: MutationCache
  #retryer?: Retryer<TData>

  constructor(config: MutationConfig<TData, TError, TVariables, TContext>) {
    super()

    this.mutationId = config.mutationId
    this.#mutationCache = config.mutationCache
    this.#observers = []
    this.state = config.state || getDefaultState()

    this.setOptions(config.options)
    this.scheduleGc()
  }

  setOptions(
    options: MutationOptions<TData, TError, TVariables, TContext>,
  ): void {
    this.options = options

    this.updateGcTime(this.options.gcTime)
  }

  get meta(): MutationMeta | undefined {
    return this.options.meta
  }

  addObserver(observer: MutationObserver<any, any, any, any>): void {
    if (!this.#observers.includes(observer)) {
      this.#observers.push(observer)

      // Stop the mutation from being garbage collected
      this.clearGcTimeout()

      this.#mutationCache.notify({
        type: 'observerAdded',
        mutation: this,
        observer,
      })
    }
  }

          }
        case 'continue':
          return {
            ...state,
            isPaused: false,
          }
        case 'pending':
          return {
            ...state,
            context: action.context,
            data: undefined,
            failureCount: 0,
            failureReason: null,
            error: null,
            isPaused: action.isPaused,
            status: 'pending',
            variables: action.variables,
            submittedAt: Date.now(),
          }
        case 'success':
          return {
            ...state,
            data: action.data,
            failureCount: 0,
            failureReason: null,
            error: null,
            status: 'success',
            isPaused: false,
          }
        case 'error':
          return {
            ...state,
            data: undefined,
            error: action.error,
            failureCount: state.failureCount + 1,
            failureReason: action.error,
            isPaused: false,
            status: 'error',
          }
      }
    }
    this.state = reducer(this.state)

    notifyManager.batch(() => {
      this.#observers.forEach((observer) => {
        observer.onMutationUpdate(action)
      })
      this.#mutationCache.notify({
        mutation: this,
        type: 'updated',
        action,
      })
    })
  }
}
// -x-
export function getDefaultState<
  TData,
  TError,
  TVariables,
  TContext,
>(): MutationState<TData, TError, TVariables, TContext> {
  return {
    context: undefined,
    data: undefined,
    error: null,
    failureCount: 0,
    failureReason: null,
    isPaused: false,
    status: 'idle',
    variables: undefined,
    submittedAt: 0,
  }
}
// -x-

import {
    functionalUpdate,
    hashKey,
    hashQueryKeyByOptions,
    noop,
    partialMatchKey,
    skipToken,
  } from './utils'
  import { QueryCache } from './queryCache'
  import { MutationCache } from './mutationCache'
  import { focusManager } from './focusManager'
  import { onlineManager } from './onlineManager'
  import { notifyManager } from './notifyManager'
  import { infiniteQueryBehavior } from './infiniteQueryBehavior'
  import type { DataTag, NoInfer, OmitKeyof } from './types'
  import type { QueryState } from './query'
  import type {
    CancelOptions,
    DefaultError,
    DefaultOptions,
    DefaultedQueryObserverOptions,
    EnsureQueryDataOptions,
    FetchInfiniteQueryOptions,
    FetchQueryOptions,
    InfiniteData,
    InvalidateOptions,
    InvalidateQueryFilters,
    MutationKey,
    MutationObserverOptions,
    MutationOptions,
    QueryClientConfig,
    QueryKey,
    QueryObserverOptions,
    QueryOptions,
    RefetchOptions,
    RefetchQueryFilters,
    ResetOptions,
    SetDataOptions,
  } from './types'
  import type { MutationFilters, QueryFilters, Updater } from './utils'
// -x-
  // TYPES
  
  interface QueryDefaults {
    queryKey: QueryKey
    defaultOptions: OmitKeyof<QueryOptions<any, any, any>, 'queryKey'>
  }
  
  interface MutationDefaults {
    mutationKey: MutationKey
    defaultOptions: MutationOptions<any, any, any, any>
  }
// -x-
  // CLASS

  export class QueryClient {
    #queryCache: QueryCache
    #mutationCache: MutationCache
    #defaultOptions: DefaultOptions
    #queryDefaults: Map<string, QueryDefaults>
    #mutationDefaults: Map<string, MutationDefaults>
    #mountCount: number
    #unsubscribeFocus?: () => void
    #unsubscribeOnline?: () => void
  
    constructor(config: QueryClientConfig = {}) {
      this.#queryCache = config.queryCache || new QueryCache()
      this.#mutationCache = config.mutationCache || new MutationCache()
      this.#defaultOptions = config.defaultOptions || {}
      this.#queryDefaults = new Map()
      this.#mutationDefaults = new Map()
      this.#mountCount = 0
    }
  
    mount(): void {
      this.#mountCount++
      if (this.#mountCount !== 1) return
  
      this.#unsubscribeFocus = focusManager.subscribe(async (focused) => {
        if (focused) {
          await this.resumePausedMutations()
          this.#queryCache.onFocus()
        }
      })
      this.#unsubscribeOnline = onlineManager.subscribe(async (online) => {
        if (online) {
          await this.resumePausedMutations()
          this.#queryCache.onOnline()
        }
      })
    }
  
    unmount(): void {
      this.#mountCount--
      if (this.#mountCount !== 0) return
  
      this.#unsubscribeFocus?.()
      this.#unsubscribeFocus = undefined
  
      this.#unsubscribeOnline?.()
      this.#unsubscribeOnline = undefined
    }
  
    isFetching(filters?: QueryFilters): number {
      return this.#queryCache.findAll({ ...filters, fetchStatus: 'fetching' })
        .length
    }
  
    isMutating(filters?: MutationFilters): number {
      return this.#mutationCache.findAll({ ...filters, status: 'pending' }).length
    }
  
    getQueryData<
      TQueryFnData = unknown,
      TTaggedQueryKey extends QueryKey = QueryKey,
      TInferredQueryFnData = TTaggedQueryKey extends DataTag<
        unknown,
        infer TaggedValue
      >
        ? TaggedValue
        : TQueryFnData,
    >(queryKey: TTaggedQueryKey): TInferredQueryFnData | undefined
    getQueryData(queryKey: QueryKey) {
      const options = this.defaultQueryOptions({ queryKey })
      return this.#queryCache.get(options.queryHash)?.state.data
    }
  
    ensureQueryData<
      TQueryFnData,
      TError = DefaultError,
      TData = TQueryFnData,
      TQueryKey extends QueryKey = QueryKey,
    >(
      options: EnsureQueryDataOptions<TQueryFnData, TError, TData, TQueryKey>,
    ): Promise<TData> {
      const cachedData = this.getQueryData<TData>(options.queryKey)
  
      if (cachedData === undefined) return this.fetchQuery(options)
      else {
        const defaultedOptions = this.defaultQueryOptions(options)
        const query = this.#queryCache.build(this, defaultedOptions)
  
        if (
          options.revalidateIfStale &&
          query.isStaleByTime(defaultedOptions.staleTime)
        ) {
          void this.prefetchQuery(defaultedOptions)
        }
  
        return Promise.resolve(cachedData)
      }
    }
  
    getQueriesData<TQueryFnData = unknown>(
      filters: QueryFilters,
    ): Array<[QueryKey, TQueryFnData | undefined]> {
      return this.#queryCache.findAll(filters).map(({ queryKey, state }) => {
        const data = state.data as TQueryFnData | undefined
        return [queryKey, data]
      })
    }
  
    setQueryData<
      TQueryFnData = unknown,
      TTaggedQueryKey extends QueryKey = QueryKey,
      TInferredQueryFnData = TTaggedQueryKey extends DataTag<
        unknown,
        infer TaggedValue
      >
        ? TaggedValue
        : TQueryFnData,
    >(
      queryKey: TTaggedQueryKey,
      updater: Updater<
        NoInfer<TInferredQueryFnData> | undefined,
        NoInfer<TInferredQueryFnData> | undefined
      >,
      options?: SetDataOptions,
    ): TInferredQueryFnData | undefined {
      const defaultedOptions = this.defaultQueryOptions<
        any,
        any,
        unknown,
        any,
        QueryKey
      >({ queryKey })
  
      const query = this.#queryCache.get<TInferredQueryFnData>(
        defaultedOptions.queryHash,
      )
      const prevData = query?.state.data
      const data = functionalUpdate(updater, prevData)
  
      if (data === undefined) {
        return undefined
      }
  
      return this.#queryCache
        .build(this, defaultedOptions)
        .setData(data, { ...options, manual: true })
    }
  
    setQueriesData<TQueryFnData>(
      filters: QueryFilters,
      updater: Updater<TQueryFnData | undefined, TQueryFnData | undefined>,
      options?: SetDataOptions,
    ): Array<[QueryKey, TQueryFnData | undefined]> {
      return notifyManager.batch(() =>
        this.#queryCache
          .findAll(filters)
          .map(({ queryKey }) => [
            queryKey,
            this.setQueryData<TQueryFnData>(queryKey, updater, options),
          ]),
      )
    }
  
    getQueryState<
      TQueryFnData = unknown,
      TError = DefaultError,
      TTaggedQueryKey extends QueryKey = QueryKey,
      TInferredQueryFnData = TTaggedQueryKey extends DataTag<
        unknown,
        infer TaggedValue
      >
        ? TaggedValue
        : TQueryFnData,
    >(
      queryKey: TTaggedQueryKey,
    ): QueryState<TInferredQueryFnData, TError> | undefined {
      const options = this.defaultQueryOptions({ queryKey })
      return this.#queryCache.get<TInferredQueryFnData, TError>(options.queryHash)
        ?.state
    }
  
    removeQueries(filters?: QueryFilters): void {
      const queryCache = this.#queryCache
      notifyManager.batch(() => {
        queryCache.findAll(filters).forEach((query) => {
          queryCache.remove(query)
        })
      })
    }
  
    resetQueries(filters?: QueryFilters, options?: ResetOptions): Promise<void> {
      const queryCache = this.#queryCache
  
      const refetchFilters: RefetchQueryFilters = {
        type: 'active',
        ...filters,
      }
  
      return notifyManager.batch(() => {
        queryCache.findAll(filters).forEach((query) => {
          query.reset()
        })
        return this.refetchQueries(refetchFilters, options)
      })
    }
  
    cancelQueries(
      filters: QueryFilters = {},
      cancelOptions: CancelOptions = {},
    ): Promise<void> {
      const defaultedCancelOptions = { revert: true, ...cancelOptions }
  
      const promises = notifyManager.batch(() =>
        this.#queryCache
          .findAll(filters)
          .map((query) => query.cancel(defaultedCancelOptions)),
      )
  
      return Promise.all(promises).then(noop).catch(noop)
    }
  
    invalidateQueries(
      filters: InvalidateQueryFilters = {},
      options: InvalidateOptions = {},
    ): Promise<void> {
      return notifyManager.batch(() => {
        this.#queryCache.findAll(filters).forEach((query) => {
          query.invalidate()
        })
  
        if (filters.refetchType === 'none') {
          return Promise.resolve()
        }
        const refetchFilters: RefetchQueryFilters = {
          ...filters,
          type: filters.refetchType ?? filters.type ?? 'active',
        }
        return this.refetchQueries(refetchFilters, options)
      })
    }
  
    refetchQueries(
      filters: RefetchQueryFilters = {},
      options?: RefetchOptions,
    ): Promise<void> {
      const fetchOptions = {
        ...options,
        cancelRefetch: options?.cancelRefetch ?? true,
      }
      const promises = notifyManager.batch(() =>
        this.#queryCache
          .findAll(filters)
          .filter((query) => !query.isDisabled())
          .map((query) => {
            let promise = query.fetch(undefined, fetchOptions)
            if (!fetchOptions.throwOnError) {
              promise = promise.catch(noop)
            }
            return query.state.fetchStatus === 'paused'
              ? Promise.resolve()
              : promise
          }),
      )
  
      return Promise.all(promises).then(noop)
    }
  
    fetchQuery<
      TQueryFnData,
      TError = DefaultError,
      TData = TQueryFnData,
      TQueryKey extends QueryKey = QueryKey,
      TPageParam = never,
    >(
      options: FetchQueryOptions<
        TQueryFnData,
        TError,
        TData,
        TQueryKey,
        TPageParam
      >,
    ): Promise<TData> {
      const defaultedOptions = this.defaultQueryOptions(options)
  
      // https://github.com/tannerlinsley/react-query/issues/652
      if (defaultedOptions.retry === undefined) {
        defaultedOptions.retry = false
      }
  
      const query = this.#queryCache.build(this, defaultedOptions)
  
      return query.isStaleByTime(defaultedOptions.staleTime)
        ? query.fetch(defaultedOptions)
        : Promise.resolve(query.state.data as TData)
    }
  
    prefetchQuery<
      TQueryFnData = unknown,
      TError = DefaultError,
      TData = TQueryFnData,
      TQueryKey extends QueryKey = QueryKey,
    >(
      options: FetchQueryOptions<TQueryFnData, TError, TData, TQueryKey>,
    ): Promise<void> {
      return this.fetchQuery(options).then(noop).catch(noop)
    }
  
    fetchInfiniteQuery<
      TQueryFnData,
      TError = DefaultError,
      TData = TQueryFnData,
      TQueryKey extends QueryKey = QueryKey,
      TPageParam = unknown,
    >(
      options: FetchInfiniteQueryOptions<
        TQueryFnData,
        TError,
        TData,
        TQueryKey,
        TPageParam
      >,
    ): Promise<InfiniteData<TData, TPageParam>> {
      options.behavior = infiniteQueryBehavior<
        TQueryFnData,
        TError,
        TData,
        TPageParam
      >(options.pages)
      return this.fetchQuery(options)
    }
  
    prefetchInfiniteQuery<
      TQueryFnData,
      TError = DefaultError,
      TData = TQueryFnData,
      TQueryKey extends QueryKey = QueryKey,
      TPageParam = unknown,
    >(
      options: FetchInfiniteQueryOptions<
        TQueryFnData,
        TError,
        TData,
        TQueryKey,
        TPageParam
      >,
    ): Promise<void> {
      return this.fetchInfiniteQuery(options).then(noop).catch(noop)
    }
  
    resumePausedMutations(): Promise<unknown> {
      if (onlineManager.isOnline()) {
        return this.#mutationCache.resumePausedMutations()
      }
      return Promise.resolve()
    }
  
    getQueryCache(): QueryCache {
      return this.#queryCache
    }
  
    getMutationCache(): MutationCache {
      return this.#mutationCache
    }
  
    getDefaultOptions(): DefaultOptions {
      return this.#defaultOptions
    }
  
    setDefaultOptions(options: DefaultOptions): void {
      this.#defaultOptions = options
    }
  
    setQueryDefaults(
      queryKey: QueryKey,
      options: Partial<
        OmitKeyof<QueryObserverOptions<unknown, any, any, any>, 'queryKey'>
      >,
    ): void {
      this.#queryDefaults.set(hashKey(queryKey), {
        queryKey,
        defaultOptions: options,
      })
    }
  
    getQueryDefaults(
      queryKey: QueryKey,
    ): OmitKeyof<QueryObserverOptions<any, any, any, any, any>, 'queryKey'> {
      const defaults = [...this.#queryDefaults.values()]
  
      let result: OmitKeyof<
        QueryObserverOptions<any, any, any, any, any>,
        'queryKey'
      > = {}
  
      defaults.forEach((queryDefault) => {
        if (partialMatchKey(queryKey, queryDefault.queryKey)) {
          result = { ...result, ...queryDefault.defaultOptions }
        }
      })
      return result
    }
  
    setMutationDefaults(
      mutationKey: MutationKey,
      options: OmitKeyof<
        MutationObserverOptions<any, any, any, any>,
        'mutationKey'
      >,
    ): void {
      this.#mutationDefaults.set(hashKey(mutationKey), {
        mutationKey,
        defaultOptions: options,
      })
    }
  
    getMutationDefaults(
      mutationKey: MutationKey,
    ): MutationObserverOptions<any, any, any, any> {
      const defaults = [...this.#mutationDefaults.values()]
  
      let result: MutationObserverOptions<any, any, any, any> = {}
  
      defaults.forEach((queryDefault) => {
        if (partialMatchKey(mutationKey, queryDefault.mutationKey)) {
          result = { ...result, ...queryDefault.defaultOptions }
        }
      })
  
      return result
    }
  
    defaultQueryOptions<
      TQueryFnData = unknown,
      TError = DefaultError,
      TData = TQueryFnData,
      TQueryData = TQueryFnData,
      TQueryKey extends QueryKey = QueryKey,
      TPageParam = never,
    >(
      options:
        | QueryObserverOptions<
            TQueryFnData,
            TError,
            TData,
            TQueryData,
            TQueryKey,
            TPageParam
          >
        | DefaultedQueryObserverOptions<
            TQueryFnData,
            TError,
            TData,
            TQueryData,
            TQueryKey
          >,
    ): DefaultedQueryObserverOptions<
      TQueryFnData,
      TError,
      TData,
      TQueryData,
      TQueryKey
    > {
      if (options._defaulted) {
        return options as DefaultedQueryObserverOptions<
          TQueryFnData,
          TError,
          TData,
          TQueryData,
          TQueryKey
        >
      }
  
      const defaultedOptions = {
        ...this.#defaultOptions.queries,
        ...this.getQueryDefaults(options.queryKey),
        ...options,
        _defaulted: true,
      }
  
      if (!defaultedOptions.queryHash) {
        defaultedOptions.queryHash = hashQueryKeyByOptions(
          defaultedOptions.queryKey,
          defaultedOptions,
        )
      }
  
      // dependent default values
      if (defaultedOptions.refetchOnReconnect === undefined) {
        defaultedOptions.refetchOnReconnect =
          defaultedOptions.networkMode !== 'always'
      }
      if (defaultedOptions.throwOnError === undefined) {
        defaultedOptions.throwOnError = !!defaultedOptions.suspense
      }
  
      if (!defaultedOptions.networkMode && defaultedOptions.persister) {
        defaultedOptions.networkMode = 'offlineFirst'
      }
  
      if (
        defaultedOptions.enabled !== true &&
        defaultedOptions.queryFn === skipToken
      ) {
        defaultedOptions.enabled = false
      }
  
      return defaultedOptions as DefaultedQueryObserverOptions<
        TQueryFnData,
        TError,
        TData,
        TQueryData,
        TQueryKey
      >
    }
  
    defaultMutationOptions<T extends MutationOptions<any, any, any, any>>(
      options?: T,
    ): T {
      if (options?._defaulted) {
        return options
      }
      return {
        ...this.#defaultOptions.mutations,
        ...(options?.mutationKey &&
          this.getMutationDefaults(options.mutationKey)),
        ...options,
        _defaulted: true,
      } as T
    }
  
    clear(): void {
      this.#queryCache.clear()
      this.#mutationCache.clear()
    }
  }
// -x-
import {
    isServer,
    isValidTimeout,
    noop,
    replaceData,
    shallowEqualObjects,
    timeUntilStale,
  } from './utils'
  import { notifyManager } from './notifyManager'
  import { focusManager } from './focusManager'
  import { Subscribable } from './subscribable'
  import { fetchState } from './query'
  import type { FetchOptions, Query, QueryState } from './query'
  import type { QueryClient } from './queryClient'
  import type {
    DefaultError,
    DefaultedQueryObserverOptions,
    PlaceholderDataFunction,
    QueryKey,
    QueryObserverBaseResult,
    QueryObserverOptions,
    QueryObserverResult,
    QueryOptions,
    RefetchOptions,
  } from './types'
// -x-
  type QueryObserverListener<TData, TError> = (
    result: QueryObserverResult<TData, TError>,
  ) => void
// -x-  
  export interface NotifyOptions {
    listeners?: boolean
  }
  
  export interface ObserverFetchOptions extends FetchOptions {
    throwOnError?: boolean
  }
// -x-  
  export class QueryObserver<
    TQueryFnData = unknown,
    TError = DefaultError,
    TData = TQueryFnData,
    TQueryData = TQueryFnData,
    TQueryKey extends QueryKey = QueryKey,
  > extends Subscribable<QueryObserverListener<TData, TError>> {
    #client: QueryClient
    #currentQuery: Query<TQueryFnData, TError, TQueryData, TQueryKey> = undefined!
    #currentQueryInitialState: QueryState<TQueryData, TError> = undefined!
    #currentResult: QueryObserverResult<TData, TError> = undefined!
    #currentResultState?: QueryState<TQueryData, TError>
    #currentResultOptions?: QueryObserverOptions<
      TQueryFnData,
      TError,
      TData,
      TQueryData,
      TQueryKey
    >
    #selectError: TError | null
    #selectFn?: (data: TQueryData) => TData
    #selectResult?: TData
    // This property keeps track of the last query with defined data.
    // It will be used to pass the previous data and query to the placeholder function between renders.
    #lastQueryWithDefinedData?: Query<TQueryFnData, TError, TQueryData, TQueryKey>
    #staleTimeoutId?: ReturnType<typeof setTimeout>
    #refetchIntervalId?: ReturnType<typeof setInterval>
    #currentRefetchInterval?: number | false
    #trackedProps = new Set<keyof QueryObserverResult>()
  
    constructor(
      client: QueryClient,
      public options: QueryObserverOptions<
        TQueryFnData,
        TError,
        TData,
        TQueryData,
        TQueryKey
      >,
    ) {
      super()
  
      this.#client = client
      this.#selectError = null
      this.bindMethods()
      this.setOptions(options)
    }
  
    protected bindMethods(): void {
      this.refetch = this.refetch.bind(this)
    }
  
    protected onSubscribe(): void {
      if (this.listeners.size === 1) {
        this.#currentQuery.addObserver(this)
  
        if (shouldFetchOnMount(this.#currentQuery, this.options)) {
          this.#executeFetch()
        } else {
          this.updateResult()
        }
  
        this.#updateTimers()
      }
    }
  
    protected onUnsubscribe(): void {
      if (!this.hasListeners()) {
        this.destroy()
      }
    }
  
    shouldFetchOnReconnect(): boolean {
      return shouldFetchOn(
        this.#currentQuery,
        this.options,
        this.options.refetchOnReconnect,
      )
    }
  
    shouldFetchOnWindowFocus(): boolean {
      return shouldFetchOn(
        this.#currentQuery,
        this.options,
        this.options.refetchOnWindowFocus,
      )
    }
  
    destroy(): void {
      this.listeners = new Set()
      this.#clearStaleTimeout()
      this.#clearRefetchInterval()
      this.#currentQuery.removeObserver(this)
    }
  
    return (
      options.enabled !== false &&
      query.state.data === undefined &&
      !(query.state.status === 'error' && options.retryOnMount === false)
    )
  }
// -x-  
  function shouldFetchOnMount(
    query: Query<any, any, any, any>,
    options: QueryObserverOptions<any, any, any, any, any>,
  ): boolean {
    return (
      shouldLoadOnMount(query, options) ||
      (query.state.data !== undefined &&
        shouldFetchOn(query, options, options.refetchOnMount))
    )
  }
// -x-  
  function shouldFetchOn(
    query: Query<any, any, any, any>,
    options: QueryObserverOptions<any, any, any, any, any>,
    field: (typeof options)['refetchOnMount'] &
      (typeof options)['refetchOnWindowFocus'] &
      (typeof options)['refetchOnReconnect'],
  ) {
    if (options.enabled !== false) {
      const value = typeof field === 'function' ? field(query) : field
  
      return value === 'always' || (value !== false && isStale(query, options))
    }
    return false
  }
// -x-  
  function shouldFetchOptionally(
    query: Query<any, any, any, any>,
    prevQuery: Query<any, any, any, any>,
    options: QueryObserverOptions<any, any, any, any, any>,
    prevOptions: QueryObserverOptions<any, any, any, any, any>,
  ): boolean {
    return (
      (query !== prevQuery || prevOptions.enabled === false) &&
      (!options.suspense || query.state.status !== 'error') &&
      isStale(query, options)
    )
  }
// -x-  
  function isStale(
    query: Query<any, any, any, any>,
    options: QueryObserverOptions<any, any, any, any, any>,
  ): boolean {
    return options.enabled !== false && query.isStaleByTime(options.staleTime)
  }
// -x-  
  // this function would decide if we will update the observer's 'current'
  // properties after an optimistic reading via getOptimisticResult
  function shouldAssignObserverCurrentProperties<
    TQueryFnData = unknown,
    TError = unknown,
    TData = TQueryFnData,
    TQueryData = TQueryFnData,
    TQueryKey extends QueryKey = QueryKey,
  >(
    observer: QueryObserver<TQueryFnData, TError, TData, TQueryData, TQueryKey>,
    optimisticResult: QueryObserverResult<TData, TError>,
  ) {
    // if the newly created result isn't what the observer is holding as current,
    // then we'll need to update the properties as well
    if (!shallowEqualObjects(observer.getCurrentResult(), optimisticResult)) {
      return true
    }
  
    // basically, just keep previous properties if nothing changed
    return false
  }
// -x-