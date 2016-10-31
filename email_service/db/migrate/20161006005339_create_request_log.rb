class CreateRequestLog < ActiveRecord::Migration
  def change
    create_table :request_logs do |t|
      t.uuid     :shared_log_id
      t.datetime :received
      t.string   :path
      t.string   :method
      t.string   :info

      t.timestamps
    end
  end

  def down
    drop_table :request_logs
  end
end
