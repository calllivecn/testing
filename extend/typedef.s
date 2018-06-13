	.file	"typedef.c"
	.globl	P
	.bss
	.align 8
	.type	P, @object
	.size	P, 8
P:
	.zero	8
	.section	.rodata
.LC0:
	.string	"a.x %d a.y %d\n"
	.align 8
.LC1:
	.string	"int p address 0x%p\n&a.x address %p\n"
.LC2:
	.string	"a string"
.LC3:
	.string	"2"
.LC4:
	.string	"const char *ch -> %s\n"
.LC5:
	.string	"&ch -> 0x%p\n"
.LC6:
	.string	"pointer ch address %p\n"
.LC7:
	.string	"P->x:%d,P->y%d\n"
	.text
	.globl	main
	.type	main, @function
main:
.LFB0:
	.cfi_startproc
	pushq	%rbp
	.cfi_def_cfa_offset 16
	.cfi_offset 6, -16
	movq	%rsp, %rbp
	.cfi_def_cfa_register 6
	subq	$32, %rsp
	movq	%fs:40, %rax
	movq	%rax, -8(%rbp)
	xorl	%eax, %eax
	movl	$123, -32(%rbp)
	movl	$456, -28(%rbp)
	leaq	-32(%rbp), %rax
	movq	%rax, -16(%rbp)
	movl	-28(%rbp), %edx
	movl	-32(%rbp), %eax
	movl	%eax, %esi
	movl	$.LC0, %edi
	movl	$0, %eax
	call	printf
	leaq	-32(%rbp), %rdx
	movq	-16(%rbp), %rax
	movq	%rax, %rsi
	movl	$.LC1, %edi
	movl	$0, %eax
	call	printf
	leaq	-32(%rbp), %rax
	movq	%rax, P(%rip)
	movq	$.LC2, -24(%rbp)
	movq	$.LC3, -24(%rbp)
	movq	-24(%rbp), %rax
	movq	%rax, %rsi
	movl	$.LC4, %edi
	movl	$0, %eax
	call	printf
	leaq	-24(%rbp), %rax
	movq	%rax, %rsi
	movl	$.LC5, %edi
	movl	$0, %eax
	call	printf
	leaq	-24(%rbp), %rax
	movq	%rax, %rsi
	movl	$.LC6, %edi
	movl	$0, %eax
	call	printf
	movq	P(%rip), %rax
	movl	$56, 4(%rax)
	movq	P(%rip), %rax
	movl	4(%rax), %edx
	movq	P(%rip), %rax
	movl	(%rax), %eax
	movl	%eax, %esi
	movl	$.LC7, %edi
	movl	$0, %eax
	call	printf
	movl	$0, %eax
	movq	-8(%rbp), %rcx
	xorq	%fs:40, %rcx
	je	.L3
	call	__stack_chk_fail
.L3:
	leave
	.cfi_def_cfa 7, 8
	ret
	.cfi_endproc
.LFE0:
	.size	main, .-main
	.ident	"GCC: (Ubuntu 5.4.0-6ubuntu1~16.04.5) 5.4.0 20160609"
	.section	.note.GNU-stack,"",@progbits
