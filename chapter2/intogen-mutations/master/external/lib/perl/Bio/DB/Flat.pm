#
# $Id: Flat.pm,v 1.6 2002/12/22 22:02:13 lstein Exp $
#
# BioPerl module for Bio::DB::Flat
#
# Cared for by Lincoln Stein <lstein@cshl.org>
#
# You may distribute this module under the same terms as perl itself

# POD documentation - main docs before the code

=head1 NAME

Bio::DB::Flat - Interface for indexed flat files

=head1 SYNOPSIS

  $db = Bio::DB::Flat->new(-directory  => '/usr/share/embl',
                           -format     => 'embl',
                           -write_flag => 1);
  $db->build_index('/usr/share/embl/primate.embl','/usr/share/embl/protists.embl');
  $seq       = $db->get_Seq_by_id('BUM');
  @sequences = $db->get_Seq_by_acc('DIV' => 'primate');
  $raw       = $db->fetch_raw('BUM');

=head1 DESCRIPTION

This object provides the basic mechanism to associate positions in
files with primary and secondary name spaces. Unlike
Bio::Index::Abstract (see L<Bio::Index::Abstract>), this is specialized
to work with the "flat index" and BerkeleyDB indexed flat file formats
worked out at the 2002 BioHackathon.

This object is a general front end to the underlying databases.

=head1 FEEDBACK

=head2 Mailing Lists

User feedback is an integral part of the evolution of this and other
Bioperl modules. Send your comments and suggestions preferably to one
of the Bioperl mailing lists.  Your participation is much appreciated.

  bioperl-l@bioperl.org             - General discussion
  http://bioperl.org/MailList.shtml - About the mailing lists

=head2 Reporting Bugs

Report bugs to the Bioperl bug tracking system to help us keep track
the bugs and their resolution.  Bug reports can be submitted via
email or the web:

  bioperl-bugs@bio.perl.org
  http://bugzilla.bioperl.org/

=head1 AUTHOR - Lincoln Stein

Email - lstein@cshl.org

=head1 APPENDIX

The rest of the documentation details each of the object methods. Internal
methods are usually preceded with an "_" (underscore).

=cut


# Let the code begin...
package Bio::DB::Flat;

use Bio::DB::RandomAccessI;
use Bio::Root::Root;
use Bio::Root::IO;
use vars '@ISA';

@ISA = qw(Bio::Root::Root Bio::DB::RandomAccessI);

use constant CONFIG_FILE_NAME => 'config.dat';

=head2 new

 Title   : new
 Usage   : my $db = new Bio::Flat->new(
                     -directory  => $root_directory,
		     -write_flag => 0,
                     -index      => 'bdb'|'flat',
                     -verbose    => 0,
		     -out        => 'outputfile',
                     -format     => 'genbank');
 Function: create a new Bio::Index::BDB object
 Returns : new Bio::Index::BDB object
 Args    : -directory    Root directory containing "config.dat"
           -write_flag   If true, allows reindexing.
           -verbose      Verbose messages
           -out          File to write to when write_seq invoked
 Status  : Public

The root -directory indicates where the flat file indexes will be
stored.  The build_index() and write_seq() methods will automatically
create a human-readable configuration file named "config.dat" in this
file.

The -write_flag enables writing new entries into the database as well
as the creation of the indexes.  By default the indexes will be opened
read only.

-index is one of "bdb" or "flat" and indicates the type of index to
generate.  "bdb" corresponds to Berkeley DB.  You *must* be using
BerkeleyDB version 2 or higher, and have the Perl BerkeleyDB extension
installed (DB_File will *not* work).

The -out argument species the output file for writing objects created
with write_seq().  

=cut

sub new {
  my $class = shift;
  $class  = ref($class) if ref($class);
  my $self = $class->SUPER::new(@_);

  # first we initialize ourselves
  my ($flat_directory) = @_ == 1 ? shift
                                 : $self->_rearrange([qw(DIRECTORY)],@_);

  # set values from configuration file
  $self->directory($flat_directory);
  $self->_read_config() if -e $flat_directory;

  # but override with initialization values
  $self->_initialize(@_);

  # now we figure out what subclass to instantiate
  my $index_type = $self->indexing_scheme eq 'BerkeleyDB/1' ? 'BDB'
                  :$self->indexing_scheme eq 'flat/1'       ? 'Flat'
                  :$self->throw("unknown indexing scheme: ".$self->indexing_scheme);
  my $format     = $self->file_format;
  my $child_class= "Bio\:\:DB\:\:Flat\:\:$index_type\:\:\L$format";
  eval "use $child_class";
  $self->throw($@) if $@;

  # rebless & reinitialize with the new class
  # (this prevents subclasses from forgetting to call our own initialization)
  bless $self,$child_class;
  $self->_initialize(@_);
  $self->_set_namespaces(@_);

  $self;
}

sub _initialize {
  my $self = shift;

  my ($flat_write_flag,$flat_indexing,$flat_verbose,$flat_outfile,$flat_format)
    = $self->_rearrange([qw(WRITE_FLAG INDEX VERBOSE OUT FORMAT)],@_);

  $self->write_flag($flat_write_flag) if defined $flat_write_flag;

  if (defined $flat_indexing) {
    # very permissive
    $flat_indexing = 'BerkeleyDB/1' if $flat_indexing =~ /bdb/;
    $flat_indexing = 'flat/1'       if $flat_indexing =~ /flat/;
    $self->indexing_scheme($flat_indexing);
  }

  $self->verbose($flat_verbose)    if defined $flat_verbose;
  $self->out_file($flat_outfile)   if defined $flat_outfile;
  $self->file_format($flat_format) if defined $flat_format;
}

sub _set_namespaces {
  my $self = shift;

  $self->primary_namespace($self->default_primary_namespace)
    unless defined $self->{flat_primary_namespace};

  $self->secondary_namespaces($self->default_secondary_namespaces)
    unless defined $self->{flat_secondary_namespaces};

  $self->file_format($self->default_file_format)
    unless defined $self->{flat_format};
}

# accessors
sub directory {
  my $self = shift;
  my $d = $self->{flat_directory};
  $self->{flat_directory} = shift if @_;
  $d;
}
sub write_flag {
  my $self = shift;
  my $d = $self->{flat_write_flag};
  $self->{flat_write_flag} = shift if @_;
  $d;
}
sub verbose {
  my $self = shift;
  my $d = $self->{flat_verbose};
  $self->{flat_verbose} = shift if @_;
  $d;
}
sub out_file {
  my $self = shift;
  my $d = $self->{flat_outfile};
  $self->{flat_outfile} = shift if @_;
  $d;
}

sub primary_namespace {
  my $self = shift;
  my $d    = $self->{flat_primary_namespace};
  $self->{flat_primary_namespace} = shift if @_;
  $d;
}

# get/set secondary namespace(s)
# pass an array ref.
# get an array ref in scalar context, list in list context.
sub secondary_namespaces {
  my $self = shift;
  my $d    = $self->{flat_secondary_namespaces};
  $self->{flat_secondary_namespaces} = (ref($_[0]) eq 'ARRAY' ? shift : [@_]) if @_;
  return unless $d;
  $d = [$d] if $d && ref($d) ne 'ARRAY';  # just paranoia
  return wantarray ? @$d : $d;
}

# return the file format
sub file_format {
  my $self = shift;
  my $d    = $self->{flat_format};
  $self->{flat_format} = shift if @_;
  $d;
}

# return the indexing scheme
sub indexing_scheme {
  my $self = shift;
  my $d    = $self->{flat_indexing};
  $self->{flat_indexing} = shift if @_;
  $d;
}

sub add_flat_file {
  my $self = shift;
  my ($file_path,$file_length,$nf) = @_;

  # check that file_path is absolute
  File::Spec->file_name_is_absolute($file_path)
      or $self->throw("the flat file path $file_path must be absolute");

  -r $file_path or $self->throw("flat file $file_path cannot be read: $!");

  my $current_size = -s _;
  if (defined $file_length) {
    $current_size == $file_length
      or $self->throw("flat file $file_path has changed size.  Was $file_length bytes; now $current_size");
  } else {
    $file_length = $current_size;
  }

  unless (defined $nf) {
    $self->{flat_file_index} = 0 unless exists $self->{flat_file_index};
    $nf = $self->{flat_file_index}++;
  }
  $self->{flat_flat_file_path}{$nf}      = $file_path;
  $self->{flat_flat_file_no}{$file_path} = $nf;
  $nf;
}

sub write_config {
  my $self = shift;
  $self->write_flag or $self->throw("cannot write configuration file because write_flag is not set");
  my $path = $self->_config_path;

  open (F,">$path") or $self->throw("open error on $path: $!");

  my $index_type = $self->indexing_scheme;
  print F "index\t$index_type\n";

  my $format     = $self->file_format;
  print F "format\t$format\n";

  my @filenos = $self->_filenos or $self->throw("cannot write config file because no flat files defined");
  for my $nf (@filenos) {
    my $path = $self->{flat_flat_file_path}{$nf};
    my $size = -s $path;
    print F join("\t","fileid_$nf",$path,$size),"\n";
  }

  # write primary namespace
  my $primary_ns = $self->primary_namespace
    or $self->throw('cannot write config file because no primary namespace defined');

  print F join("\t",'primary_namespace',$primary_ns),"\n";

  # write secondary namespaces
  my @secondary = $self->secondary_namespaces;
  print F join("\t",'secondary_namespaces',@secondary),"\n";

  close F or $self->throw("close error on $path: $!");
}

sub files {
  my $self = shift;
  return unless $self->{flat_flat_file_no};
  return keys %{$self->{flat_flat_file_no}};
}

sub write_seq {
  my $self  = shift;
  my $seq   = shift;

  $self->write_flag or $self->throw("cannot write sequences because write_flag is not set");

  my $file  = $self->out_file or $self->throw('no outfile defined; use the -out argument to new()');
  my $seqio = $self->{flat_cached_parsers}{$file}
    ||= Bio::SeqIO->new(-Format => $self->file_format,
			-file   => ">$file")
      or $self->throw("couldn't create Bio::SeqIO object");

  my $fh = $seqio->_fh or $self->throw("couldn't get filehandle from Bio::SeqIO object");
  my $offset    = tell($fh);
  $seqio->write_seq($seq);
  my $length    = tell($fh)-$offset;
  my $ids       = $self->seq_to_ids($seq);
  $self->_store_index($ids,$file,$offset,$length);

  $self->{flat_outfile_dirty}++;
}

sub close {
  my $self = shift;
  return unless $self->{flat_outfile_dirty};
  $self->write_config;
  delete $self->{flat_outfile_dirty};
  delete $self->{flat_cached_parsers}{$self->out_file};
}


sub _filenos {
  my $self = shift;
  return unless $self->{flat_flat_file_path};
  return keys %{$self->{flat_flat_file_path}};
}

# read the configuration file
sub _read_config {
  my $self   = shift;
  my $config = shift;

  my $path = defined $config ? Bio::Root::IO->catfile($config,CONFIG_FILE_NAME) 
                             : $self->_config_path;
  return unless -e $path;

  open (F,$path) or $self->throw("open error on $path: $!");
  my %config;
  while (<F>) {
    chomp;
    my ($tag,@values) = split "\t";
    $config{$tag} = \@values;
  }
  CORE::close F or $self->throw("close error on $path: $!");

  $config{index}[0] =~ m~(flat/1|BerkeleyDB/1)~
    or $self->throw("invalid configuration file $path: no index line");

  $self->indexing_scheme($1);

  $self->file_format($config{format}[0]) if $config{format};

  # set up primary namespace
  my $primary_namespace = $config{primary_namespace}[0]
    or $self->throw("invalid configuration file $path: no primary namespace defined");
  $self->primary_namespace($primary_namespace);

  # set up secondary namespaces (may be empty)
  $self->secondary_namespaces($config{secondary_namespaces});

  # get file paths and their normalization information
  my @normalized_files = grep {$_ ne ''} map {/^fileid_(\S+)/ && $1} keys %config;
  for my $nf (@normalized_files) {
    my ($file_path,$file_length) = @{$config{"fileid_${nf}"}};
    $self->add_flat_file($file_path,$file_length,$nf);
  }
  1;
}


sub _config_path {
  my $self = shift;
  $self->_catfile($self->_config_name);
}

sub _catfile {
  my $self = shift;
  my $component = shift;
  Bio::Root::IO->catfile($self->directory,$component);
}

sub _config_name { CONFIG_FILE_NAME }

sub _path2fileno {
  my $self = shift;
  my $path = shift;
  return $self->add_flat_file($path)
    unless exists $self->{flat_flat_file_no}{$path};
  $self->{flat_flat_file_no}{$path};
}

sub _fileno2path {
  my $self = shift;
  my $fileno = shift;
  $self->{flat_flat_file_path}{$fileno};
}

sub _files {
  my $self = shift;
  my $paths = $self->{flat_flat_file_no};
  return keys %$paths;
}

=head2 fetch

  Title   : fetch
  Usage   : $index->fetch( $id )
  Function: Returns a Bio::Seq object from the index
  Example : $seq = $index->fetch( 'dJ67B12' )
  Returns : Bio::Seq object
  Args    : ID

Deprecated.  Use get_Seq_by_id instead.

=cut

sub fetch { shift->get_Seq_by_id(@_) }


=head2 To Be Implemented in Subclasses

The following methods MUST be implemented by subclasses.

=cut

# create real live Bio::Seq object
sub get_Seq_by_id {
  my $self = shift;
  my $id   = shift;
  $self->throw_not_implemented;
}


# fetch array of Bio::Seq objects
sub get_Seq_by_acc {
  my $self = shift;
  return $self->get_Seq_by_id(shift) if @_ == 1;
  my ($ns,$key) = @_;

  $self->throw_not_implemented;
}

sub fetch_raw {
  my ($self,$id,$namespace) = @_;
  $self->throw_not_implemented;
}

# This is the method that must be implemented in
# child classes.  It is passed a filehandle which should
# point to the next record to be indexed in the file, 
# and returns a two element list
# consisting of a key and an adjustment value.
# The key can be a scalar, in which case it is treated
# as the primary ID, or a hashref containing namespace=>[id] pairs,
# one of which MUST correspond to the primary namespace.
# The adjustment value is normally zero, but can be a positive or
# negative integer which will be added to the current file position
# in order to calculate the correct end of the record.
sub parse_one_record {
  my $self = shift;
  my $fh   = shift;
  $self->throw_not_implemented;
  # here's what you would implement
  my (%keys,$offset);
  return (\%keys,$offset);
}

sub default_file_format {
  my $self = shift;
  $self->throw_not_implemented;
}

sub _store_index {
   my ($ids,$file,$offset,$length) = @_;
   $self->throw_not_implemented;
}

=head2 May Be Overridden in Subclasses

The following methods MAY be overridden by subclasses.

=cut

sub default_primary_namespace {
  return "ACC";
}

sub default_secondary_namespaces {
  return;
}

sub seq_to_ids {
  my $self = shift;
  my $seq  = shift;
  my %ids;
  $ids{$self->primary_namespace} = $seq->accession_number;
  \%ids;
}

sub DESTROY {
  my $self = shift;
  $self->close;
}


1;
