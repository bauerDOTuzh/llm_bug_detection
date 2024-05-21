# frozen_string_literal: true

module SidekiqUniqueJobs
    #
    # Class BatchDelete provides batch deletion of digests
    #
    # @author Mikael Henriksson <mikael@mhenrixon.com>
    #
    class BatchDelete
      #
      # @return [Integer] the default batch size
      BATCH_SIZE = 100
  
      #
      # @return [Array<String>] Supported key suffixes
      SUFFIXES = %w[
        QUEUED
        PRIMED
        LOCKED
        INFO
      ].freeze
  
      # includes "SidekiqUniqueJobs::Connection"
      # @!parse include SidekiqUniqueJobs::Connection
      include SidekiqUniqueJobs::Connection
      # includes "SidekiqUniqueJobs::Logging"
      # @!parse include SidekiqUniqueJobs::Logging
      include SidekiqUniqueJobs::Logging
  
      #
      # @!attribute [r] digests
      #   @return [Array<String>] a collection of digests to be deleted
      attr_reader :digests
      #
      # @!attribute [r] conn
      #   @return [Redis, RedisConnection, ConnectionPool] a redis connection
      attr_reader :conn
  
      #
      # Executes a batch deletion of the provided digests
      #
      # @param [Array<String>] digests the digests to delete
      # @param [Redis] conn the connection to use for deletion
      #
      # @return [void]
      #
      def self.call(digests, conn = nil)
        new(digests, conn).call
      end
  
      #
      # Initialize a new batch delete instance
      #
      # @param [Array<String>] digests the digests to delete
      # @param [Redis] conn the connection to use for deletion
      #
      def initialize(digests, conn)
        @count   = 0
        @digests = digests
        @conn    = conn
        @digests ||= []
        @digests.compact!
        redis_version # Avoid pipelined calling redis_version and getting a future.
      end
  
      #
      # Executes a batch deletion of the provided digests
      # @note Just wraps batch_delete to be able to provide no connection
      #
      #
      def call
        return log_info("Nothing to delete; exiting.") if digests.none?
  
        log_info("Deleting batch with #{digests.size} digests")
        return batch_delete(conn) if conn
  
        redis { |rcon| batch_delete(rcon) }
      end
  
      private
  
      #
      # Does the actual batch deletion
      #
      #
      # @return [Integer] the number of deleted digests
      #
      def batch_delete(conn)
        digests.each_slice(BATCH_SIZE) do |chunk|
          conn.pipelined do |pipeline|
            chunk.each do |digest|
              del_digest(pipeline, digest)
              pipeline.zrem(SidekiqUniqueJobs::DIGESTS, digest)
              pipeline.zrem(SidekiqUniqueJobs::EXPIRING_DIGESTS, digest)
              @count += 1
            end
          end
        end
  
        @count
      end
  
      def del_digest(pipeline, digest)
        removable_keys = keys_for_digest(digest)
  
        pipeline.unlink(*removable_keys)
      end
  
      def keys_for_digest(digest)
        [digest, "#{digest}:RUN"].each_with_object([]) do |key, digest_keys|
          digest_keys.push(key)
          digest_keys.concat(SUFFIXES.map { |suffix| "#{key}:#{suffix}" })
        end
      end
  
      def redis_version
        @redis_version ||= SidekiqUniqueJobs.config.redis_version
      end
    end
  end

# -x-
# frozen_string_literal: true

module SidekiqUniqueJobs
    #
    # Class Changelogs provides access to the changelog entries
    #
    # @author Mikael Henriksson <mikael@mhenrixon.com>
    #
    class Changelog < Redis::SortedSet
      def initialize
        super(CHANGELOGS)
      end
  
      #
      # Adds a new changelog entry
      #
      # @param [String] message a descriptive message about the entry
      # @param [String] digest a unique digest
      # @param [String] job_id a Sidekiq JID
      # @param [String] script the name of the script adding the entry
      #
      # @return [void]
      #
      def add(message:, digest:, job_id:, script:)
        message = dump_json(message: message, digest: digest, job_id: job_id, script: script)
        redis { |conn| conn.zadd(key, now_f, message) }
      end
  
      #
      # The change log entries
      #
      # @param [String] pattern the pattern to match
      # @param [Integer] count the number of matches to return
      #
      # @return [Array<Hash>] an array of entries
      #
      def entries(pattern: SCAN_PATTERN, count: DEFAULT_COUNT)
        redis do |conn|
          conn.zscan(key, match: pattern, count: count).to_a.map { |entry| load_json(entry[0]) }
        end
      end
  
      #
      # Paginate the changelog entries
      #
      # @param [Integer] cursor the cursor for this iteration
      # @param [String] pattern "*" the pattern to match
      # @param [Integer] page_size 100 the number of matches to return
      #
      # @return [Array<Integer, Integer, Array<Hash>] the total size, next cursor and changelog entries
      #
      def page(cursor: 0, pattern: "*", page_size: 100)
        redis do |conn|
          total_size, result = conn.multi do |pipeline|
            pipeline.zcard(key)
            pipeline.zscan(key, cursor, match: pattern, count: page_size)
          end
  
          # NOTE: When debugging, check the last item in the returned array.
          [
            total_size.to_i,
            result[0].to_i, # next_cursor
            result[1].map { |entry| load_json(entry) }.select { |entry| entry.is_a?(Hash) },
          ]
        end
      end
    end
  end
# -x-
# frozen_string_literal: true

require "thor"

module SidekiqUniqueJobs
  #
  # Command line interface for unique jobs
  #
  # @author Mikael Henriksson <mikael@mhenrixon.com>
  #
  class Cli < Thor
    # :nodoc:
    # rubocop:disable Style/OptionalBooleanParameter
    def self.banner(command, _namespace = nil, _subcommand = false) # rubocop:disable Style/OptionalBooleanParameter
      "jobs #{@package_name} #{command.usage}" # rubocop:disable ThreadSafety/InstanceVariableInClassMethod
    end
    # rubocop:enable Style/OptionalBooleanParameter

    desc "list PATTERN", "list all unique digests and their expiry time"
    option :count, aliases: :c, type: :numeric, default: 1000, desc: "The max number of digests to return"
    # :nodoc:
    def list(pattern = "*")
      max_count = options[:count]
      say "Searching for regular digests"
      list_entries(digests.entries(pattern: pattern, count: max_count), pattern)
      say "Searching for expiring digests"
      list_entries(expiring_digests.entries(pattern: pattern, count: max_count), pattern)
    end

    desc "del PATTERN", "deletes unique digests from redis by pattern"
    option :dry_run, aliases: :d, type: :boolean, desc: "set to false to perform deletion"
    option :count, aliases: :c, type: :numeric, default: 1000, desc: "The max number of digests to return"
    # :nodoc:
    def del(pattern)
      max_count = options[:count]
      if options[:dry_run]
        count_entries_for_del(max_count, pattern)
      else
        del_entries(max_count, pattern)
      end
    end

    desc "console", "drop into a console with easy access to helper methods"
    # :nodoc:
    def console
      say "Use `list '*', 1000 to display the first 1000 unique digests matching '*'"
      say "Use `del '*', 1000, true (default) to see how many digests would be deleted for the pattern '*'"
      say "Use `del '*', 1000, false to delete the first 1000 digests matching '*'"

      # Object.include SidekiqUniqueJobs::Api
      console_class.start
    end

    no_commands do # rubocop:disable Metrics/BlockLength
      # :nodoc:
      def digests
        @digests ||= SidekiqUniqueJobs::Digests.new
      end

      # :nodoc:
      def expiring_digests
        @expiring_digests ||= SidekiqUniqueJobs::ExpiringDigests.new
      end

      # :nodoc:
      def console_class
        require "pry"
        Pry
      rescue NameError, LoadError
        require "irb"
        IRB
      end

      # :nodoc:
      def list_entries(entries, pattern)
        say "Found #{entries.size} digests matching '#{pattern}':"
        print_in_columns(entries.sort) if entries.any?
      end

      # :nodoc:
      def count_entries_for_del(max_count, pattern)
        count = digests.entries(pattern: pattern, count: max_count).size +
                expiring_digests.entries(pattern: pattern, count: max_count).size
        say "Would delete #{count} digests matching '#{pattern}'"
      end

      # :nodoc:
      def del_entries(max_count, pattern)
        deleted_count = digests.delete_by_pattern(pattern, count: max_count).to_i +
                        expiring_digests.delete_by_pattern(pattern, count: max_count).to_i
        say "Deleted #{deleted_count} digests matching '#{pattern}'"
      end
    end
  end
end
# -x-
# frozen_string_literal: true

module SidekiqUniqueJobs
    # ThreadSafe config exists to be able to document the config class without errors
    ThreadSafeConfig = Concurrent::MutableStruct.new("ThreadSafeConfig",
                                                     :lock_timeout,
                                                     :lock_ttl,
                                                     :enabled,
                                                     :lock_prefix,
                                                     :logger,
                                                     :logger_enabled,
                                                     :locks,
                                                     :strategies,
                                                     :debug_lua,
                                                     :max_history,
                                                     :reaper,
                                                     :reaper_count,
                                                     :reaper_interval,
                                                     :reaper_timeout,
                                                     :reaper_resurrector_interval,
                                                     :reaper_resurrector_enabled,
                                                     :lock_info,
                                                     :raise_on_config_error,
                                                     :current_redis_version)
  
    #
    # Shared class for dealing with gem configuration
    #
    # @author Mauro Berlanda <mauro.berlanda@gmail.com>
    # rubocop:disable Metrics/ClassLength
    class Config < ThreadSafeConfig
      #
      # @return [Hash<Symbol, SidekiqUniqueJobs::Lock::BaseLock] all available queued locks
      LOCKS_WHILE_ENQUEUED = {
        until_executing: SidekiqUniqueJobs::Lock::UntilExecuting,
        while_enqueued: SidekiqUniqueJobs::Lock::UntilExecuting,
      }.freeze
  
      #
      # @return [Hash<Symbol, SidekiqUniqueJobs::Lock::BaseLock] all available fulltime locks
      LOCKS_FROM_PUSH_TO_PROCESSED = {
        until_completed: SidekiqUniqueJobs::Lock::UntilExecuted,
        until_executed: SidekiqUniqueJobs::Lock::UntilExecuted,
        until_performed: SidekiqUniqueJobs::Lock::UntilExecuted,
        until_processed: SidekiqUniqueJobs::Lock::UntilExecuted,
        until_and_while_executing: SidekiqUniqueJobs::Lock::UntilAndWhileExecuting,
        until_successfully_completed: SidekiqUniqueJobs::Lock::UntilExecuted,
      }.freeze
  
      #
      # @return [Hash<Symbol, SidekiqUniqueJobs::Lock::BaseLock] all available locks without unlock
      LOCKS_WITHOUT_UNLOCK = {
        until_expired: SidekiqUniqueJobs::Lock::UntilExpired,
      }.freeze
  
      #
      # @return [Hash<Symbol, SidekiqUniqueJobs::Lock::BaseLock] all available runtime/client locks
      LOCKS_WHEN_BUSY = {
        around_perform: SidekiqUniqueJobs::Lock::WhileExecuting,
        while_busy: SidekiqUniqueJobs::Lock::WhileExecuting,
        while_executing: SidekiqUniqueJobs::Lock::WhileExecuting,
        while_working: SidekiqUniqueJobs::Lock::WhileExecuting,
        while_executing_reject: SidekiqUniqueJobs::Lock::WhileExecutingReject,
      }.freeze
  
      #
      # @return [Hash<Symbol, SidekiqUniqueJobs::Lock::BaseLock] all available default locks
      LOCKS =
        LOCKS_WHEN_BUSY.dup
                       .merge(LOCKS_WHILE_ENQUEUED.dup)
                       .merge(LOCKS_WITHOUT_UNLOCK.dup)
                       .merge(LOCKS_FROM_PUSH_TO_PROCESSED.dup)
                       .freeze
  
      #
      # @return [Hash<Symbol, SidekiqUniqueJobs::OnConflict::Strategy] all available default strategies
      STRATEGIES = {
        log: SidekiqUniqueJobs::OnConflict::Log,
        raise: SidekiqUniqueJobs::OnConflict::Raise,
        reject: SidekiqUniqueJobs::OnConflict::Reject,
        replace: SidekiqUniqueJobs::OnConflict::Replace,
        reschedule: SidekiqUniqueJobs::OnConflict::Reschedule,
      }.freeze
  
      #
      # @return ['uniquejobs'] by default we use this prefix
      PREFIX                = "uniquejobs"
      #
      # @return [0] by default don't wait for locks
      LOCK_TIMEOUT          = 0
      #
      # @return [nil]
      LOCK_TTL              = nil
      #
      # @return [true,false] by default false (don't disable logger)
      LOGGER_ENABLED        = true
      #
      # @return [true] by default the gem is enabled
      ENABLED               = true
      #
      # @return [false] by default we don't debug the lua scripts because it is slow
      DEBUG_LUA             = false
      #
      # @return [1_000] use a changelog history of 1_000 entries by default
      MAX_HISTORY           = 1_000
      #
      # @return [:ruby] prefer the ruby reaper by default since the lua reaper still has problems
      REAPER                = :ruby
      #
      # @return [1_000] reap 1_000 orphaned locks at a time by default
      REAPER_COUNT          = 1_000
      #
      # @return [600] reap locks every 10 minutes
      REAPER_INTERVAL       = 600
      #
      # @return [10] stop reaper after 10 seconds
      REAPER_TIMEOUT        = 10
      #
      # @return [3600] check if reaper is dead each 3600 seconds
      REAPER_RESURRECTOR_INTERVAL = 3600
  
      #
      # @return [false] enable reaper resurrector
      REAPER_RESURRECTOR_ENABLED = false
  
      #
      # @return [false] while useful it also adds overhead so disable lock_info by default
      USE_LOCK_INFO         = false
      #
      # @return [false] by default we don't raise validation errors for workers
      RAISE_ON_CONFIG_ERROR = false
      #
      # @return [0.0.0] default redis version is only to avoid NoMethodError on nil
      REDIS_VERSION         = "0.0.0"
  
      #
      # Returns a default configuration
      #
      # @example
      #   SidekiqUniqueJobs::Config.default => <concurrent/mutable_struct/thread_safe_config SidekiqUniqueJobs::Config {
      #   default_lock_timeout: 0,
      #   default_lock_ttl: nil,
      #   enabled: true,
      #   lock_prefix: "uniquejobs",
      #   logger: #<Sidekiq::Logger:0x00007f81e096b0e0 @level=1 ...>,
      #   locks: {
      #     around_perform: SidekiqUniqueJobs::Lock::WhileExecuting,
      #     while_busy: SidekiqUniqueJobs::Lock::WhileExecuting,
      #     while_executing: SidekiqUniqueJobs::Lock::WhileExecuting,
      #     while_working: SidekiqUniqueJobs::Lock::WhileExecuting,
      #     while_executing_reject: SidekiqUniqueJobs::Lock::WhileExecutingReject,
      #     until_executing: SidekiqUniqueJobs::Lock::UntilExecuting,
      #     while_enqueued: SidekiqUniqueJobs::Lock::UntilExecuting,
      #     until_expired: SidekiqUniqueJobs::Lock::UntilExpired,
      #     until_completed: SidekiqUniqueJobs::Lock::UntilExecuted,
      #     until_executed: SidekiqUniqueJobs::Lock::UntilExecuted,
      #     until_performed: SidekiqUniqueJobs::Lock::UntilExecuted,
      #     until_processed: SidekiqUniqueJobs::Lock::UntilExecuted,
      #     until_and_while_executing: SidekiqUniqueJobs::Lock::UntilAndWhileExecuting,
      #     until_successfully_completed: SidekiqUniqueJobs::Lock::UntilExecuted
      #   },
      #   strategies: {
      #     log: SidekiqUniqueJobs::OnConflict::Log,
      #     raise: SidekiqUniqueJobs::OnConflict::Raise,
      #     reject: SidekiqUniqueJobs::OnConflict::Reject,
      #     replace: SidekiqUniqueJobs::OnConflict::Replace,
      #     reschedule: SidekiqUniqueJobs::OnConflict::Reschedule
      #   },
      #   debug_lua: false,
      #   max_history: 1000,
      #   reaper:: ruby,
      #   reaper_count: 1000,
      #   lock_info: false,
      #   raise_on_config_error: false,
      #   }>
      #
      #
      # @return [SidekiqUniqueJobs::Config] a default configuration
      #
      def self.default # rubocop:disable Metrics/MethodLength
        new(
          LOCK_TIMEOUT,
          LOCK_TTL,
          ENABLED,
          PREFIX,
          Sidekiq.logger,
          LOGGER_ENABLED,
          LOCKS,
          STRATEGIES,
          DEBUG_LUA,
          MAX_HISTORY,
          REAPER,
          REAPER_COUNT,
          REAPER_INTERVAL,
          REAPER_TIMEOUT,
          REAPER_RESURRECTOR_INTERVAL,
          REAPER_RESURRECTOR_ENABLED,
          USE_LOCK_INFO,
          RAISE_ON_CONFIG_ERROR,
          REDIS_VERSION,
        )
      end
  
      #
      # Set the default_lock_ttl
      # @deprecated
      #
      # @param [Integer] obj value to set (seconds)
      #
      # @return [<type>] <description>
      #
      def default_lock_ttl=(obj)
        warn "[DEPRECATION] `#{class_name}##{__method__}` is deprecated." \
             " Please use `#{class_name}#lock_ttl=` instead."
        self.lock_ttl = obj
      end
  
      #
      # Set new value for default_lock_timeout
      # @deprecated
      #
      # @param [Integer] obj value to set (seconds)
      #
      # @return [Integer]
      #
      def default_lock_timeout=(obj)
        warn "[DEPRECATION] `#{class_name}##{__method__}` is deprecated." \
             " Please use `#{class_name}#lock_timeout=` instead."
        self.lock_timeout = obj
      end
  
      #
      # Default lock TTL (Time To Live)
      # @deprecated
      #
      # @return [nil, Integer] configured value or nil
      #
      def default_lock_ttl
        warn "[DEPRECATION] `#{class_name}##{__method__}` is deprecated." \
             " Please use `#{class_name}#lock_ttl` instead."
        lock_ttl
      end
  
      #
      # Default Lock Timeout
      # @deprecated
      #
      #
      # @return [nil, Integer] configured value or nil
      #
      def default_lock_timeout
        warn "[DEPRECATION] `#{class_name}##{__method__}` is deprecated." \
             " Please use `#{class_name}#lock_timeout` instead."
        lock_timeout
      end
  
      #
      # Memoized variable to get the class name
      #
      #
      # @return [String] name of the class
      #
      def class_name
        @class_name ||= self.class.name
      end
  
      #
      # Adds a lock type to the configuration. It will raise if the lock exists already
      #
      # @example Add a custom lock
      #   add_lock(:my_lock, CustomLocks::MyLock)
      #
      # @raise DuplicateLock when the name already exists
      #
      # @param [String, Symbol] name the name of the lock
      # @param [Class] klass the class describing the lock
      #
      # @return [void]
      #
      def add_lock(name, klass)
        lock_sym = name.to_sym
        raise DuplicateLock, ":#{name} already defined, please use another name" if locks.key?(lock_sym)
  
        new_locks = locks.dup.merge(lock_sym => klass).freeze
        self.locks = new_locks
      end
  
      #
      # Adds an on_conflict strategy to the configuration.
      #
      # @example Add a custom strategy
      #   add_lock(:my_strategy, CustomStrategies::MyStrategy)
      #
      # @raise [DuplicateStrategy] when the name already exists
      #
      # @param [String] name the name of the custom strategy
      # @param [Class] klass the class describing the strategy
      #
      def add_strategy(name, klass)
        strategy_sym = name.to_sym
        raise DuplicateStrategy, ":#{name} already defined, please use another name" if strategies.key?(strategy_sym)
  
        new_strategies = strategies.dup.merge(strategy_sym => klass).freeze
        self.strategies = new_strategies
      end
  
      #
      # The current version of redis
      #
      #
      # @return [String] a version string eg. `5.0.1`
      #
      def redis_version
        self.current_redis_version = SidekiqUniqueJobs.fetch_redis_version if current_redis_version == REDIS_VERSION
        current_redis_version
      end
    end
    # rubocop:enable Metrics/ClassLength
  end
# -x-
# frozen_string_literal: true

module SidekiqUniqueJobs
    # Shared module for dealing with redis connections
    #
    # @author Mikael Henriksson <mikael@mhenrixon.com>
    module Connection
      def self.included(base)
        base.send(:extend, self)
      end
  
      # Creates a connection to redis
      # @return [Sidekiq::RedisConnection] a connection to redis
      def redis(_r_pool = nil, &block)
        Sidekiq.redis do |conn|
          conn.with(&block)
        end
      end
    end
  end
# -x-
# frozen_string_literal: true

#
# Module with constants to avoid string duplication
#
# @author Mikael Henriksson <mikael@mhenrixon.com>
#
module SidekiqUniqueJobs
    ARGS                  = "args"
    APARTMENT             = "apartment"
    AT                    = "at"
    CHANGELOGS            = "uniquejobs:changelog"
    CLASS                 = "class"
    CREATED_AT            = "created_at"
    DEAD_VERSION          = "uniquejobs:dead"
    DIGESTS               = "uniquejobs:digests"
    EXPIRING_DIGESTS      = "uniquejobs:expiring_digests"
    ERRORS                = "errors"
    JID                   = "jid"
    LIMIT                 = "limit"
    LIVE_VERSION          = "uniquejobs:live"
    LOCK                  = "lock"
    LOCK_ARGS             = "lock_args"
    LOCK_ARGS_METHOD      = "lock_args_method"
    LOCK_DIGEST           = "lock_digest"
    LOCK_EXPIRATION       = "lock_expiration"
    LOCK_INFO             = "lock_info"
    LOCK_LIMIT            = "lock_limit"
    LOCK_PREFIX           = "lock_prefix"
    LOCK_TIMEOUT          = "lock_timeout"
    LOCK_TTL              = "lock_ttl"
    LOCK_TYPE             = "lock_type"
    ON_CLIENT_CONFLICT    = "on_client_conflict"
    ON_CONFLICT           = "on_conflict"
    ON_SERVER_CONFLICT    = "on_server_conflict"
    PAYLOAD               = "payload"
    PROCESSES             = "processes"
    QUEUE                 = "queue"
    RETRY                 = "retry"
    SCHEDULE              = "schedule"
    TIME                  = "time"
    TIMEOUT               = "timeout"
    TTL                   = "ttl"
    TYPE                  = "type"
    UNIQUE                = "unique"
    UNIQUE_ACROSS_QUEUES  = "unique_across_queues"
    UNIQUE_ACROSS_WORKERS = "unique_across_workers"
    UNIQUE_ARGS           = "unique_args"
    UNIQUE_ARGS_METHOD    = "unique_args_method"
    UNIQUE_DIGEST         = "unique_digest"
    UNIQUE_PREFIX         = "unique_prefix"
    UNIQUE_REAPER         = "uniquejobs:reaper"
    WORKER                = "worker"
  end
# -x-
# frozen_string_literal: true

# :nocov:

#
# Monkey patches for the ruby Hash
#
class Hash
    unless {}.respond_to?(:slice)
      #
      # Returns only the matching keys in a new hash
      #
      # @param [Array<String>, Array<Symbol>] keys the keys to match
      #
      # @return [Hash]
      #
      def slice(*keys)
        keys.map! { |key| convert_key(key) } if respond_to?(:convert_key, true)
        keys.each_with_object(self.class.new) { |k, hash| hash[k] = self[k] if key?(k) }
      end
    end
  
    unless {}.respond_to?(:deep_stringify_keys)
      #
      # Depp converts all keys to string
      #
      #
      # @return [Hash<String>]
      #
      def deep_stringify_keys
        deep_transform_keys(&:to_s)
      end
    end
  
    unless {}.respond_to?(:deep_transform_keys)
      #
      # Deep transfor all keys by yielding to the caller
      #
      #
      # @return [Hash<String>]
      #
      def deep_transform_keys(&block)
        _deep_transform_keys_in_object(self, &block)
      end
    end
  
    unless {}.respond_to?(:stringify_keys)
      #
      # Converts all keys to string
      #
      #
      # @return [Hash<String>]
      #
      def stringify_keys
        transform_keys(&:to_s)
      end
    end
  
    unless {}.respond_to?(:transform_keys)
      #
      # Transforms all keys by yielding to the caller
      #
      #
      # @return [Hash]
      #
      def transform_keys
        result = {}
        each_key do |key|
          result[yield(key)] = self[key]
        end
        result
      end
    end
  
    unless {}.respond_to?(:slice!)
      #
      # Removes all keys not provided from the current hash and returns it
      #
      # @param [Array<String>, Array<Symbol>] keys the keys to match
      #
      # @return [Hash]
      #
      def slice!(*keys)
        keys.map! { |key| convert_key(key) } if respond_to?(:convert_key, true)
        omit = slice(*self.keys - keys)
        hash = slice(*keys)
        hash.default      = default
        hash.default_proc = default_proc if default_proc
        replace(hash)
        omit
      end
    end
  
    private
  
    unless {}.respond_to?(:_deep_transform_keys_in_object)
      # support methods for deep transforming nested hashes and arrays
      def _deep_transform_keys_in_object(object, &block)
        case object
        when Hash
          object.each_with_object(self.class.new) do |(key, value), result|
            result[yield(key)] = _deep_transform_keys_in_object(value, &block)
          end
        when Array
          object.map { |element| _deep_transform_keys_in_object(element, &block) }
        else
          object
        end
      end
    end
  end
  
  #
  # Monkey patches for the ruby Array
  #
  class Array
    unless [].respond_to?(:extract_options!)
      #
      # Extract the last argument if it is a hash
      #
      #
      # @return [Hash]
      #
      def extract_options!
        if last.is_a?(Hash) && last.instance_of?(Hash)
          pop
        else
          {}
        end
      end
    end
  end
# -x-
# frozen_string_literal: true

module SidekiqUniqueJobs
    #
    # Class Deprecation provides logging of deprecations
    #
    # @author Mikael Henriksson <mikael@mhenrixon.com>
    #
    class Deprecation
      #
      # Mute warnings from this gem in a threaded context
      #
      #
      # @return [void] <description>
      #
      # @yieldreturn [void]
      def self.muted
        orig_val = Thread.current[:uniquejobs_mute_deprecations]
        Thread.current[:uniquejobs_mute_deprecations] = true
        yield
      ensure
        Thread.current[:uniquejobs_mute_deprecations] = orig_val
      end
  
      #
      # Check if deprecation warnings have been muted
      #
      #
      # @return [true,false]
      #
      def self.muted?
        Thread.current[:uniquejobs_mute_deprecations] == true
      end
  
      #
      # Warn about deprecation
      #
      # @param [String] msg a descriptive reason for why the deprecation
      #
      # @return [void]
      #
      def self.warn(msg)
        return if SidekiqUniqueJobs::Deprecation.muted?
  
        warn "DEPRECATION WARNING: #{msg}"
        nil
      end
  
      #
      # Warn about deprecation and provide a context
      #
      # @param [String] msg a descriptive reason for why the deprecation
      #
      # @return [void]
      #
      def self.warn_with_backtrace(msg)
        return if SidekiqUniqueJobs::Deprecation.muted?
  
        trace = "\n\nCALLED FROM:\n#{caller.join("\n")}"
        warn(msg + trace)
  
        nil
      end
    end
  end
# -x-
# frozen_string_literal: true

module SidekiqUniqueJobs
    #
    # Class Changelogs provides access to the changelog entries
    #
    # @author Mikael Henriksson <mikael@mhenrixon.com>
    #
    class Digests < Redis::SortedSet
      #
      # @return [Integer] the number of matches to return by default
      DEFAULT_COUNT = 1_000
      #
      # @return [String] the default pattern to use for matching
      SCAN_PATTERN  = "*"
      #
      # @return [Array(String, String, String, String)] The empty runtime or queuetime keys.
      EMPTY_KEYS_SEGMENT = ["", "", "", ""].freeze
  
      def initialize(digests_key = DIGESTS)
        super(digests_key)
      end
  
      #
      # Adds a digest
      #
      # @param [String] digest the digest to add
      #
      def add(digest)
        redis { |conn| conn.zadd(key, now_f, digest) }
      end
  
      # Deletes unique digests by pattern
      #
      # @param [String] pattern a key pattern to match with
      # @param [Integer] count the maximum number
      # @return [Hash<String,Float>] Hash mapping of digest matching the given pattern and score
  
      def delete_by_pattern(pattern, count: DEFAULT_COUNT)
        result, elapsed = timed do
          digests = entries(pattern: pattern, count: count).keys
          redis { |conn| BatchDelete.call(digests, conn) }
        end
  
        log_info("#{__method__}(#{pattern}, count: #{count}) completed in #{elapsed}ms")
  
        result
      end
  
      # Delete unique digests by digest
      #   Also deletes the :AVAILABLE, :EXPIRED etc keys
      #
      # @param [String] digest a unique digest to delete
      # @param queuetime [Boolean] Whether to delete queue locks.
      # @param runtime [Boolean] Whether to delete run locks.
      def delete_by_digest(digest, queuetime: true, runtime: true)
        result, elapsed = timed do
          call_script(
            :delete_by_digest,
            queuetime_keys(queuetime ? digest : nil) + runtime_keys(runtime ? digest : nil) + [key],
          )
        end
  
        log_info("#{__method__}(#{digest}) completed in #{elapsed}ms")
  
        result
      end
  
      #
      # The entries in this sorted set
      #
      # @param [String] pattern SCAN_PATTERN the match pattern to search for
      # @param [Integer] count DEFAULT_COUNT the number of entries to return
      #
      # @return [Array<String>] an array of digests matching the given pattern
      #
      def entries(pattern: SCAN_PATTERN, count: DEFAULT_COUNT)
        redis { |conn| conn.zscan(key, match: pattern, count: count).to_a }.to_h
      end
  
      #
      # Returns a paginated
      #
      # @param [Integer] cursor the cursor for this iteration
      # @param [String] pattern SCAN_PATTERN the match pattern to search for
      # @param [Integer] page_size 100 the size per page
      #
      # @return [Array<Integer, Integer, Array<Lock>>] total_size, next_cursor, locks
      #
      def page(cursor: 0, pattern: SCAN_PATTERN, page_size: 100)
        redis do |conn|
          total_size, digests = conn.multi do |pipeline|
            pipeline.zcard(key)
            pipeline.zscan(key, cursor, match: pattern, count: page_size)
          end
  
          # NOTE: When debugging, check the last item in the returned array.
          [
            total_size.to_i,
            digests[0].to_i, # next_cursor
            digests[1].each_slice(2).map { |digest, score| Lock.new(digest, time: score) }, # entries
          ]
        end
      end
  
      private
  
      # @param digest [String, nil] The digest to form runtime keys from.
      # @return [Array(String, String, String, String)] The list of runtime keys or empty strings if +digest+ was +nil+.
      def runtime_keys(digest)
        return EMPTY_KEYS_SEGMENT unless digest
  
        [
          "#{digest}:RUN",
          "#{digest}:RUN:QUEUED",
          "#{digest}:RUN:PRIMED",
          "#{digest}:RUN:LOCKED",
        ]
      end
  
      # @param digest [String, nil] The digest to form queuetime keys from.
      # @return [Array(String, String, String, String)] The list of queuetime keys or empty strings if +digest+ was +nil+.
      def queuetime_keys(digest)
        return EMPTY_KEYS_SEGMENT unless digest
  
        [
          digest,
          "#{digest}:QUEUED",
          "#{digest}:PRIMED",
          "#{digest}:LOCKED",
        ]
      end
    end
  end
# -x-