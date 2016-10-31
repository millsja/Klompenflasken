require 'rspec'
require 'securerandom'
require_relative '../../app'
require_relative '../../models/error_log'

describe ErrorLog do
  it 'has expected fields' do
    expected_fields = [:shared_log_id, :received, :path, :method, :info]

    error_log_params = {
      shared_log_id: SecureRandom.uuid,
      received: Time.now,
      path: '/fake/path',
      method: 'GET',
      info: 'woops'
    }

    created_error_log = ErrorLog.new(error_log_params)

    expected_fields.each do |field|
      expect(created_error_log.respond_to?(field)).to be true
    end
  end
end
