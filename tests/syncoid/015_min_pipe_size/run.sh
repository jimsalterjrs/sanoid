#!/bin/bash

# unit test for buildsynccmd(): transfers below $minpipesize must skip compression
# and mbuffer, larger ones (and unknown-size ones) must keep the full pipeline.
# no zpool needed - the sub is extracted from syncoid and evaluated directly.

set -e

exec perl -x "$0" ../../../syncoid
exit $?

#!perl
use strict;
use warnings;

my $syncoid = shift or die "usage: run.sh /path/to/syncoid\n";

# globals buildsynccmd() reads, set up to mimic a real run
our ($sourcehost, $targethost) = ('', 'root@target');
our %avail = ('compress' => 1, 'sourcembuffer' => 1, 'targetmbuffer' => 1, 'localmbuffer' => 1, 'localpv' => 1);
our %args = ('source-bwlimit' => '', 'target-bwlimit' => '');
our %compressargs = ('cmd' => 'lzop', 'decomcmd' => 'lzop -dfc');
our $mbuffercmd = 'mbuffer';
our $mbufferoptions = '-q -s 128k -m 16M';
our $pvcmd = 'pv';
our $pvoptions = '-p -t -e -r -b';
our $socatcmd = 'socat';
our $sshcmd = 'ssh';
our $quiet = 0;
our ($directconnect, $directlisten, $directtimeout, $directmbuffer) = ('', '', 60, 0);
our $minpipesize;

# pull buildsynccmd(), escapeshellparam() and $minpipesize out of syncoid itself,
# so this test breaks if the real implementation changes behaviour
open my $fh, '<', $syncoid or die "cannot read $syncoid: $!";
my $src = do { local $/; <$fh> };
close $fh;

my ($size) = $src =~ /^my \$minpipesize = (.*);$/m or die "no \$minpipesize in $syncoid\n";
$minpipesize = eval $size;

my @subs;
foreach my $name ('buildsynccmd', 'escapeshellparam') {
	my ($body) = $src =~ /^(sub \Q$name\E \{.*?^\})$/ms or die "no sub $name in $syncoid\n";
	push @subs, $body;
}
eval join("\n", @subs);
die "cannot load subs: $@" if $@;

my $failed = 0;
sub check {
	my ($desc, $pvsize, $want) = @_;
	my $cmd = buildsynccmd('zfs send -I a b', 'zfs receive -s -F t', $pvsize, 1, 1);
	foreach my $stage ('lzop', 'mbuffer') {
		my $got = ($cmd =~ /\b\Q$stage\E\b/) ? 1 : 0;
		next if $got == $want;
		print "FAIL: $desc: expected " . ($want ? '' : 'no ') . "$stage in: $cmd\n";
		$failed = 1;
	}
	# pv is not size gated - progress reporting stays either way
	if ($cmd !~ /\bpv\b/) {
		print "FAIL: $desc: pv missing from: $cmd\n";
		$failed = 1;
	}
}

check('small transfer', $minpipesize - 1, 0);
check('threshold transfer', $minpipesize, 1);
check('large transfer', 100 * $minpipesize, 1);
check('unknown size', 0, 1);

print $failed ? "FAILED\n" : "PASS\n";
exit $failed;
