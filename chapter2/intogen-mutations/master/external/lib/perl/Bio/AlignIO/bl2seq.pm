# $Id: bl2seq.pm,v 1.13.2.1 2003/06/18 12:19:52 jason Exp $
#
# BioPerl module for Bio::AlignIO::bl2seq

#	based on the Bio::SeqIO modules
#       by Ewan Birney <birney@sanger.ac.uk>
#       and Lincoln Stein  <lstein@cshl.org>
#
#	the Bio::Tools::BPlite modules by
#	Ian Korf (ikorf@sapiens.wustl.edu, http://sapiens.wustl.edu/~ikorf),
#	Lorenz Pollak (lorenz@ist.org, bioperl port)
#
#       and the SimpleAlign.pm module of Ewan Birney
#
# Copyright Peter Schattner
#
# You may distribute this module under the same terms as perl itself
# _history
# September 5, 2000
# POD documentation - main docs before the code

=head1 NAME

Bio::AlignIO::bl2seq - bl2seq sequence input/output stream

=head1 SYNOPSIS

Do not use this module directly.  Use it via the L<Bio::AlignIO> class, as in:

    use Bio::AlignIO;

    $in  = Bio::AlignIO->new(-file => "inputfilename" , '-format' => 'bl2seq');
    $aln = $in->next_aln();


=head1 DESCRIPTION

This object can create L<Bio::SimpleAlign> sequence alignment objects (of
2 sequences) from bl2seq BLAST reports.

A nice feature of this module is that- in combination with
StandAloneBlast.pm or remote blasting - it can be used to align 2
sequences and make a SimpleAlign object from them which can then be
manipulated using any SimpleAlign.pm methods, eg:

   #Get 2 sequences
   $str = Bio::SeqIO->new(-file=>'t/amino.fa' , '-format' => 'Fasta', );
   my $seq3 = $str->next_seq();
   my $seq4 = $str->next_seq();

   # Run bl2seq on them
   $factory = Bio::Tools::StandAloneBlast->new('program' => 'blastp', 
					       'outfile' => 'bl2seq.out');
   my $bl2seq_report = $factory->bl2seq($seq3, $seq4);

   # Use AlignIO.pm to create a SimpleAlign object from the bl2seq report
   $str = Bio::AlignIO->new(-file=> 'bl2seq.out','-format' => 'bl2seq');
   $aln = $str->next_aln();

   Pass in -report_type flag when initializing the object to have this
   pass through to the Bio::Tools::BPbl2seq object.  See that object.

=head1 FEEDBACK

=head2 Mailing Lists

User feedback is an integral part of the evolution of this and other
Bioperl modules. Send your comments and suggestions preferably to one
of the Bioperl mailing lists.  Your participation is much appreciated.

  bioperl-l@bioperl.org               - General discussion
  http://bio.perl.org/MailList.html   - About the mailing lists

=head2 Reporting Bugs

Report bugs to the Bioperl bug tracking system to help us keep track
 the bugs and their resolution.
 Bug reports can be submitted via email or the web:

  bioperl-bugs@bio.perl.org
  http://bugzilla.bioperl.org/

=head1 AUTHOR - Peter Schattner

Email: schattner@alum.mit.edu


=head1 APPENDIX

The rest of the documentation details each of the object
methods. Internal methods are usually preceded with a _

=cut

# Let the code begin...

package Bio::AlignIO::bl2seq;
use vars qw(@ISA);
use strict;
# Object preamble - inherits from Bio::Root::Object

use Bio::AlignIO;
use Bio::Tools::BPbl2seq;

@ISA = qw(Bio::AlignIO);



sub _initialize {
    my ($self,@args) = @_;
    $self->SUPER::_initialize(@args);
    ($self->{'report_type'}) = $self->_rearrange([qw(REPORT_TYPE)],
						 @args);
    return 1;
}

=head2 next_aln

 Title   : next_aln
 Usage   : $aln = $stream->next_aln()
 Function: returns the next alignment in the stream.
 Returns : L<Bio::Align::AlignI> object - returns 0 on end of file
	    or on error
 Args    : NONE

=cut

sub next_aln {
    my $self = shift;
    my ($start,$end,$name,$seqname,$seq,$seqchar);
    my $aln =  Bio::SimpleAlign->new(-source => 'bl2seq');
    $self->{'bl2seqobj'} =
    	$self->{'bl2seqobj'} || Bio::Tools::BPbl2seq->new(-fh => $self->_fh,
							  -report_type => $self->{'report_type'});
    my $bl2seqobj = $self->{'bl2seqobj'};
    my $hsp =   $bl2seqobj->next_feature;
    $seqchar = $hsp->querySeq;
    $start = $hsp->query->start;
    $end = $hsp->query->end;
    $seqname = 'Query-sequence';    # Query name not present in bl2seq report

#    unless ($seqchar && $start && $end  && $seqname) {return 0} ;	
    unless ($seqchar && $start && $end ) {return 0} ;	

    $seq = new Bio::LocatableSeq('-seq'=>$seqchar,
				 '-id'=>$seqname,
				 '-start'=>$start,
				 '-end'=>$end,
				 );

    $aln->add_seq($seq);

    $seqchar = $hsp->sbjctSeq;
    $start = $hsp->hit->start;
    $end = $hsp->hit->end;
    $seqname = $bl2seqobj->sbjctName;

    unless ($seqchar && $start && $end  && $seqname) {return 0} ;	

    $seq = new Bio::LocatableSeq('-seq'=>$seqchar,
				 '-id'=>$seqname,
				 '-start'=>$start,
				 '-end'=>$end,
				 );

    $aln->add_seq($seq);

    return $aln;

}
	

=head2 write_aln

 Title   : write_aln
 Usage   : $stream->write_aln(@aln)
 Function: writes the $aln object into the stream in bl2seq format
 Returns : 1 for success and 0 for error
 Args    : L<Bio::Align::AlignI> object


=cut

sub write_aln {
    my ($self,@aln) = @_;

    $self->throw("Sorry: writing bl2seq output is not available! /n");
}

1;
