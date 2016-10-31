# This file is auto-generated from the current state of the database. Instead
# of editing this file, please use the migrations feature of Active Record to
# incrementally modify your database, and then regenerate this schema definition.
#
# Note that this schema.rb definition is the authoritative source for your
# database schema. If you need to create the application database on another
# system, you should be using db:schema:load, not running all the migrations
# from scratch. The latter is a flawed and unsustainable approach (the more migrations
# you'll amass, the slower it'll run and the greater likelihood for issues).
#
# It's strongly recommended that you check this file into your version control system.

ActiveRecord::Schema.define(version: 20161007021609) do

  # These are extensions that must be enabled in order to support this database
  enable_extension "plpgsql"

  create_table "error_logs", force: :cascade do |t|
    t.uuid     "shared_log_id"
    t.datetime "received"
    t.string   "path"
    t.string   "method"
    t.string   "info"
    t.datetime "created_at"
    t.datetime "updated_at"
  end

  create_table "request_logs", force: :cascade do |t|
    t.uuid     "shared_log_id"
    t.datetime "received"
    t.string   "path"
    t.string   "method"
    t.string   "info"
    t.datetime "created_at"
    t.datetime "updated_at"
  end

  create_table "sent_certificates", force: :cascade do |t|
    t.string   "to_email"
    t.string   "award_name"
    t.string   "encoded_attachment"
    t.datetime "created_at"
    t.datetime "updated_at"
  end

end
