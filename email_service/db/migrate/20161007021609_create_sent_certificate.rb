class CreateSentCertificate < ActiveRecord::Migration
  def change
    create_table :sent_certificates do |t|
      t.string :to_email
      t.string :award_name
      t.string :encoded_attachment

      t.timestamps
    end
  end

  def down
    drop_table :sent_certificates
  end
end
