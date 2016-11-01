require 'json'

class MissingFieldsError
  def initialize(errors)
    @errors = errors
  end

  def render
    body = {
      status_code: 422,
      response: "Unprocessable Entity",
      errors: []
    }

    @errors.each do |e|
      body[:errors] << "#{e}"
    end

    body.to_json
  end
end
