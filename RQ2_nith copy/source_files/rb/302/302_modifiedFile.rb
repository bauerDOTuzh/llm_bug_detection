# frozen_string_literal: true
# -x-
require_relative "web/helpers"
# -x-
module SidekiqUniqueJobs
  # Utility module to help manage unique keys in redis.
  # Useful for deleting keys that for whatever reason wasn't deleted
  # @author Mikael Henriksson <mikael@mhenrixon.com>
  module Web
    def self.registered(app) # rubocop:disable Metrics/MethodLength, Metrics/AbcSize, Metrics/CyclomaticComplexity, Metrics/PerceivedComplexity
      app.helpers do
        include Web::Helpers
      end

      register_changelog_route(app)
      register_delete_changelog_route(app)
      register_delete_locks_route(app)
    end
  end
end
# -x-
def register_delete_changelog_route(app)
  app.get "/changelogs/delete_all" do
    changelog.clear
    redirect_to :changelogs
  end
end
# -x-
def register_delete_locks_route(app)
  app.get "/locks/delete_all" do
    digests.delete_by_pattern("*", count: digests.count)
    expiring_digests.delete_by_pattern("*", count: digests.count)
    redirect_to :locks
  end
end
# -x-
begin
  require "delegate" unless defined?(DelegateClass)
  require "sidekiq/web" unless defined?(Sidekiq::Web)

  Sidekiq::Web.register(SidekiqUniqueJobs::Web)
  Sidekiq::Web.tabs["Locks"] = "locks"
  Sidekiq::Web.tabs["Expiring Locks"] = "expiring_locks"
  Sidekiq::Web.tabs["Changelogs"] = "changelogs"
  Sidekiq::Web.settings.locales << File.join(File.dirname(__FILE__), "locales")
rescue NameError, LoadError => ex
  SidekiqUniqueJobs.logger.error(ex)
end
# -x-