
create table filename(filename text,size int);

insert into filename(filename,size)
		select filename,size
		from sha
		where filename is (
						select filename
						from sha
						group by filename having count(*)>1
						);

create table size(filename text,size int);

insert into size(filename,size)
	select filename,size
	from filename
	where size is (
					select size
					from filename
					group by size having count(*)>1);

drop table filename;

select * from size;



create table filesize(filename text,size int);

create table tmp1(filename text,size int);


insert into tmp1(filename,size)
	select filename,size
	from sha
	where size is (select size from sha group by size having count(*)>1);

insert into filesize(filename,size)
	select filename,size
	from tmp1
	where filename is (select filename from tmp1 group by filename having count(*)>1);

drop table tmp1;

select * from filesize;

