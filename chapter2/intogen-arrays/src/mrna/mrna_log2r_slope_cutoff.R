
# Load an expression matrix
# Creates a copy in Rdata format to accelerate future loadings

load.matrix <- function(file, rdata=TRUE) {

	file_rdata <- paste(file, "Rdata", sep=".")

	if (rdata == TRUE & file.exists(file_rdata)) {
		load(file_rdata)
	}
	else {
		em <- read.table(file=file, sep="\t", header=TRUE, row.names=1, na.strings="-")
		if (rdata == TRUE) save(em, file=file_rdata)
	}
	
	return(em)
}

# Calculate probabilities for a set of cutoffs
# cutoffs and data values should be in the same units

calculate_probabilities <- function(em, fcs, cond) {

	num_fcs <- length(fcs)

	p <- numeric(num_fcs)
	
	j <- 1
	k <- 1

	values <- as.vector(as.matrix(em))
	values <- values[!is.na(values)]
	n1 <- length(values)
		
	if (cond == "upreg") {
		fcs <- sort(fcs)
		values <- values[values >= fcs[1]]
		values <- sort(values)
		n2 <- length(values)
		
		while ((j <= n2) & (k <= num_fcs)) {
			if (values[j] < fcs[k]) {
				j <- j + 1
			} else {
				p[k] <- (n2 - j + 1) / n1
				k <- k + 1
			}
		}
		
		if (k <= num_fcs) p[k:num_fcs] <- 0

	} else {
		fcs <- sort(fcs)
		values <- values[values <= fcs[num_fcs]]
		values <- sort(values)
		n2 <- length(values)
		
		while ((j <= n2) & (k <= num_fcs)) {
			if (values[j] < fcs[k]) {
				j <- j + 1
			} else {
				p[k] <- (j) / n1
				k <- k + 1
			}
		}
		
		if (k <= num_fcs) p[k:num_fcs] <- n2 / n1
	}
	
	return (p)
}

find_cutoff_from_slope <- function(fcs, p, slope, cond) {
	model <- smooth.spline(fcs, p)
	x <- seq(fcs[1], fcs[length(fcs)], 0.001)
	s <- predict(model, x, deriv=1)$y
	
	if (cond == "upreg") {
		i <- 1
		while (i < length(s) & s[i] < slope) i <- i + 1
	} else {
		i <- length(s)
		while (i > 0 & s[i] > slope) i <- i - 1
	}

	return (list(cutoff=x[i], x=x, s=s))
}

plot.p_and_slope <- function(fcs, p, sx, s, cutoff, cond, slope, file, title="p and slope") {

	postscript(file=file, paper="a4", title=title, horizontal=F)
	
	file_part <- unlist(strsplit(basename(file), "[.]"))
	title <- paste("cond = ", cond, ", slope = ", slope, ", cutoff = ", cutoff, sep="")

	xlim <- c(min(fcs), max(fcs))
	xlab <- expression(Log[2]~Ratio)
	
	cl <- "red"
	cc <- "blue"
	
	par(mfrow=c(2, 1))
	
	plot(p, type="n", xlim=xlim, xlab=xlab, ylab="p", main=title)
	abline(v=cutoff, col=cc)
	#abline(h=0, col="grey90")
	abline(h=seq(0, 1, 0.1), col="grey90")
	abline(v=seq(-10, 10, 0.5), col="grey90")
	lines(fcs, p, col=cl)

	plot(s, type="n", xlim=xlim, xlab=xlab, ylab="slope")
	#abline(h=0, col="grey90")
	abline(h=c(0.1, 0.05, 0.025, 0, -0.025, -0.05, -0.1), col="grey90")
	abline(v=seq(-10, 10, 0.5), col="grey90")
	points(cutoff, slope)
	x <- c(xlim[1], cutoff, cutoff)
	y <- c(slope, slope, -100000)
	lines(x, y, col=cc)
	lines(sx, s, col=cl)

	par(mfrow=c(1, 1))
	
	do <- dev.off()
}

# --------------------------------------------------------------

args <- commandArgs(TRUE)

ifile <- args[1]				# expression matrix path
cond <- args[2]					# condition
slope <- as.numeric(args[3])	# slope
cutoff_file <- args[4]			# cutoff output file
plot_file <- args[5]			# plot output file

if (cond == "upreg") {
	fcs <- log2(seq(1, 99.9, 0.1))
	decreasing <- FALSE
} else if (cond == "downreg") {
	fcs <- log2(seq(0.01, 1, 0.01))
	decreasing <- TRUE
	slope <- slope * -1
} else {
	q(status = -1)
}

em <- load.matrix(ifile)

p <- calculate_probabilities(em, fcs, cond)

x <- find_cutoff_from_slope(fcs, p, slope, cond)

if (file.create(cutoff_file)) {
	f <- file(cutoff_file, "w")
	cat(as.character(x$cutoff), file=f, sep="")
	close(f)
} else {
	q(status = -1)
}

plot.p_and_slope(fcs, p, x$x, x$s, x$cutoff, cond, slope, file=plot_file)

