#!/usr/bin/perl

use Data::Dumper;

my %hash;

$hash{'one'} = 1;
$hash{'two'} = 2;
$hash{'one'}{'a'} = "1a";
$hash{'oneb'} = "1b";

dumphash(\%hash);

exit 0;

sub dumphash() {
	my $hash = shift;
	$Data::Dumper::Sortkeys = 1;
	print Dumper($hash);
}

