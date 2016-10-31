class SentCertificate < ActiveRecord::Base
  def self.sent_before?(params)
    where(to_email: params['email']).where(award_name: params['award'])
  end
end
