require 'sinatra'
require 'sinatra/activerecord'
require 'json'
require 'securerandom'

require './config/environments'
require './models/request_log'
require './models/error_log'
require './models/sent_certificate'
require './services/latex_service'
require './services/email_service'

get "/health" do
  'Latex service really healthy'
end

get "/logs/errors" do
  @logs = ErrorLog.all
  erb :'logs/errors'
end

get "/logs/requests" do
  @logs = RequestLog.all
  erb :'logs/requests'
end

get "/logs/:id" do
  @id = params['id']
  @requests = RequestLog.where(shared_log_id: @id)
  @errors = ErrorLog.where(shared_log_id: @id)
  erb :'logs/show'
end

post "/generate" do
  post_params = JSON.parse(request.body.read)
  post_params_for_logs = post_params.clone
  post_params_for_logs['awarder_signature'] = 'Hidden base64 encoding'

  log_params = {
    shared_log_id: SecureRandom.uuid,
    method: request.request_method,
    path: request.request_method,
    received: Time.now
  }

  RequestLog.new(log_params.merge(info: post_params_for_logs)).save
  maybe_sent_before = SentCertificate.sent_before?(
    email: post_params['recipient_email'],
    award: post_params['award_type']
  )

  if maybe_sent_before.size == 1
    sent_certificate = maybe_sent_before.first
    RequestLog.new(log_params.merge(info: 'resending certificate')).save
    email = EmailService.new(
      to: sent_certificate.to_email,
      award: sent_certificate.award_name,
    )

    email.build_attachment(
      sent_certificate.encoded_attachment,
      "#{sent_certificate.award_name}.pdf"
    )

    email_response = email.send

    unless email_response.status_code == '202'
      email_errors = JSON.parse(email_response.body)['errors'].first
      ErrorLog.new(log_params.merge(info: email_errors)).save

      content_type :json
      halt 404, email_errors.to_json
    end
  else
    errors = LatexService.validate_params(post_params)

    unless errors.nil?
      ErrorLog.new(log_params.merge(info: errors.render)).save
      content_type :json
      halt 422, errors.render
    end

    latex = LatexService.new(post_params)
    pdf_path = latex.generate_pdf
    email = EmailService.new(
      to: post_params['recipient_email'],
      award: post_params['award_type']
    )
    email.build_attachment(pdf_path)

    email_response = email.send

    unless email_response.status_code == '202'
      email_errors = JSON.parse(email_response.body)['errors'].first
      ErrorLog.new(log_params.merge(info: email_errors)).save

      content_type :json
      halt 404, email_errors.to_json
    end

    SentCertificate.new(
      to_email: post_params['recipient_email'],
      award_name: post_params['award_type'],
      encoded_attachment: email.attachment.content
    ).save
  end
end
