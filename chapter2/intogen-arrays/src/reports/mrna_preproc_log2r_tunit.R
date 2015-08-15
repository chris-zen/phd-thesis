args <- commandArgs(TRUE)

base_path = args[1]
id = args[2]
data_path = args[3]

m <- as.matrix(read.table(file=data_path, sep="\t", header=TRUE, row.names=1, na.strings="-"))

numcols = dim(m)[2]
colnames(m) = 1:numcols

# log2r boxplot per sample

png(file=paste(base_path, "/", id, "-l2r-boxplot.png", sep=""))
bp = boxplot(m, outline=F, xlab="sample", ylab=expression(log[2]~ratio))
title("log2r boxplot per sample")
do = dev.off()

# log2r density plot per sample

xmin = min(bp$stats[1,])
xmax = max(bp$stats[5,])

for (i in 1:numcols) {
	png(height=100, file=paste(base_path, "/", id, "-l2r-density-", as.character(i), ".png", sep=""))

	if (i == numcols) {
		par(mar=c(5.1,4.1,0,0))
	}
	else {
		par(mar=c(0,4.1,0,0))
	}

	plot(density(m[,i], na.rm=TRUE, from=xmin, to=xmax), xlim=c(xmin,xmax), main="", axes=F, ylab=as.character(i), xlab="")

	if (i == numcols) {
		axis(1)
	}
	else {
	}

	do = dev.off()
}
