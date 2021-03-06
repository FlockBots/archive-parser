if __FILE__ != $0
  abort '! This script is intended to be used only via the command line.'
end

require 'optparse'
require_relative 'parser'
require_relative 'database'

def parse_args
  defaults = {source: 'archive.csv',
              target: 'archive.db',
              date: Date.new(1970,1,1)}
  options = {}
  OptionParser.new do |opts|
    opts.banner = "Usage #{__FILE__} [options]"

    opts.on("-sSOURCE", "--source=SOURCE", "CSV file to read from") do |v|
      options[:source] = v
    end
    opts.on("-tTARGET", "--target=TARGET", "SQLite database to save to") do |v|
      options[:target] = v
    end
    opts.on("-dDATE", "--date=DATE",
        "Skip reviews archived before this date (%Y-%m-%d)") do |v|
      options[:date] = Date.strptime(v, '%Y-%m-%d')
    end

    opts.on("-h", "--help", "Prints this help") do
      puts opts
      exit
    end
  end.parse!
  defaults.merge options
end

args = parse_args
source = args[:source]
target = args[:target]
min_age = args[:date]

parser = Parser.new(source)
database = Database::setup(target)

logfile = File.join(__dir__, 'cli.log')
logger = Logger.new(logfile)

parser.records.each do |record|
  if record.archived_at < min_age
    next
  end
  if record.invalid?
    logger.error "Skipping #{record.url}"
    next
  end

  review = Database::Review.new
  review.whisky = record.whisky
  review.region = record.region
  review.redditor = record.redditor
  review.url = record.url
  review.subreddit = record.subreddit
  review.rating = record.rating
  review.region = record.region
  review.published_at = record.published_at
  begin
    if !review.save
      logger.error(review.errors.inspect)
    end
  rescue DataObjects::IntegrityError
    logger.debug "#{record.redditor},#{record.url} already exists."
  end
end
