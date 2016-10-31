require 'rspec'
require 'securerandom'
require_relative '../../app'
require_relative '../../models/request_log'

describe RequestLog do
  it 'has expected fields' do
    expected_fields = [:shared_log_id, :received, :path, :method, :info]

    request_log_params = {
      shared_log_id: SecureRandom.uuid,
      received: Time.now,
      path: '/fake/path',
      method: 'GET',
      info: 'success!'
    }

    created_request_log = RequestLog.new(request_log_params)

    expected_fields.each do |field|
      expect(created_request_log.respond_to?(field)).to be true
    end
  end
end
