require 'prawn'
require 'date'
require 'base64'
require_relative '../models/missing_fields_error'

class LatexService
  LATEX_FIELDS = [
    "recipient_first_name",
    "recipient_last_name",
    "recipient_email",
    "award_date",
    "award_type",
    "awarder_first_name",
    "awarder_last_name",
    "awarder_signature"
  ]

  def initialize(params)
    LATEX_FIELDS.each do |f|
      instance_variable_set("@#{f}", params[f])
    end
  end

  def generate_pdf
    pdf = 'certificate.pdf'
    recipient = recipient_full_name
    awarder = awarder_full_name
    signature = decode_signature
    award = @award_type
    date = @award_date.to_time.strftime("%B %d, %Y")

    Prawn::Document.generate(pdf, page_layout: :landscape, :background => "./background.png") do
      move_down 50
      text award, align: :center, size: 42
      move_down 10
      text "Awarded to #{recipient}", align: :center, size: 30
      move_down 10
      text "On #{date}", align: :center, size: 24

      stroke do
        horizontal_line 480, 650, at: 75
      end

      image signature, vposition: 390, position: 500, width: 150

      move_down 225

      text_box s = awarder, at: [500, 60], size: 18
    end

    pdf
  end

  def self.validate_params(params)
    errors = []

    LATEX_FIELDS.each do |f|
      errors << "Missing field: #{f}" if params[f].nil?
    end

    date = params["award_date"]
    errors << "Invalid date format: #{date}" unless valid_date?(date)

    MissingFieldsError.new(errors) unless errors.empty?
  end

  private

  def recipient_full_name
    "#{@recipient_first_name} #{@recipient_last_name}"
  end

  def awarder_full_name
    "#{@awarder_first_name} #{@awarder_last_name}"
  end

  def decode_signature
    signature = @awarder_signature
    signature_path = 'signature.jpg'

    File.open(signature_path, 'wb') do |f|
      f.write(Base64.decode64(signature))
    end

    signature_path
  end

  def self.valid_date?(date)
    return false if date.nil?

    begin
      Date.parse(date)
      true
    rescue ArgumentError
      false
    end
  end
end
