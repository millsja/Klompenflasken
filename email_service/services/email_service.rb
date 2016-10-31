require 'sendgrid-ruby'
require 'base64'

class EmailService
  include SendGrid

  attr_accessor :attachment, :to

  def initialize(params)
    @sg = SendGrid::API.new(api_key: ENV['SENDGRID_API_KEY'])
    @to = Email.new(email: params[:to])
    @from = Email.new(email: 'nate.f.piche@gmail.com')
    @subject = "Congratulations on your #{params[:award]}! award"
    @content = Content.new(
      type: 'text/plain',
      value: "Please see attachment for your certificate"
    )
  end

  def send
    mail = Mail.new(@from, @subject, @to, @content)
    mail.attachments = @attachment
    @sg.client.mail._('send').post(request_body: mail.to_json)
  end

  def build_attachment(b64_encoded = nil, path)
    b64_encoded ||= Base64.strict_encode64(open(path) { |io| io.read })

    @attachment = Attachment.new
    @attachment.type = 'application/pdf'
    @attachment.filename = path
    @attachment.content_id = 'Certficate'
    @attachment.content = b64_encoded
  end
end
