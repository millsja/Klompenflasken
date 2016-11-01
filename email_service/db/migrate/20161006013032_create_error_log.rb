class CreateErrorLog < ActiveRecord::Migration
  def change
    create_table :error_logs do |t|
      t.uuid     :shared_log_id
      t.datetime :received
      t.string   :path
      t.string   :method
      t.string   :info

      t.timestamps
    end
  end

  def down
    drop_table :error_logs
  end
end
