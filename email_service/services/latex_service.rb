require 'prawn'
require 'date'
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
    pdf = Prawn::Document.new
    pdf.text "#{@recipient_first_name} #{@recipient_last_name}"
    pdf.text "#{Date.parse(@award_date)} #{@recipient_email} #{@award_type}"
    pdf.text "#{@awarder_first_name} #{@awarder_last_name} #{@awarder_signature}"
    pdf.render_file("Test.pdf")
    return "Test.pdf"
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
